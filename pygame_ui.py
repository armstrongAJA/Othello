import os
import sys
import time
import math
import logging
try:
    import pygame
except Exception:
    pygame = None

from Board import spaceState

logger = logging.getLogger(__name__)


class PygameUI:
    def __init__(self, game, cell_size=90):
        if pygame is None:
            raise ImportError('pygame is required for PygameUI')
        self.game = game
        self.cell_size = cell_size
        self.size = game.board.size
        self.top_bar_height = 54
        self.board_top = self.top_bar_height
        self.window_margin = 140
        self.width = self.size * self.cell_size
        self.height = self.board_top + self.size * self.cell_size + self.window_margin

        pygame.init()
        pygame.display.set_caption('Othello')
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 32)

        # Menu state
        self.black_mode = 'Human'
        self.white_mode = 'Human'
        self.ai_depth = 2
        self.running = True
        self.in_menu = True
        self.game_over = False
        self.game_over_text = ''
        self._top_buttons = []
        self._game_over_buttons = []

        # Animation queue: list of dicts describing in-progress piece animations
        self._animations = []

    def _lerp_color(self, color_a, color_b, t):
        return (
            int(color_a[0] + (color_b[0] - color_a[0]) * t),
            int(color_a[1] + (color_b[1] - color_a[1]) * t),
            int(color_a[2] + (color_b[2] - color_a[2]) * t),
        )

    def _draw_vertical_gradient(self, rect, top_color, bottom_color):
        if rect.height <= 1:
            pygame.draw.rect(self.screen, top_color, rect)
            return
        for i in range(rect.height):
            t = i / max(1, rect.height - 1)
            color = self._lerp_color(top_color, bottom_color, t)
            pygame.draw.line(self.screen, color, (rect.left, rect.top + i), (rect.right - 1, rect.top + i))

    def _draw_cell(self, x, y):
        left = x * self.cell_size
        top = self.board_top + y * self.cell_size
        outer_rect = pygame.Rect(left, top, self.cell_size, self.cell_size)
        inner_rect = outer_rect.inflate(-4, -4)

        self._draw_vertical_gradient(outer_rect, (46, 122, 62), (34, 96, 48))
        self._draw_vertical_gradient(inner_rect, (34, 110, 52), (26, 78, 40))
        pygame.draw.line(self.screen, (76, 156, 88), outer_rect.topleft, outer_rect.topright, 1)
        pygame.draw.line(self.screen, (18, 54, 28), outer_rect.bottomleft, outer_rect.bottomright, 1)
        pygame.draw.line(self.screen, (76, 156, 88), outer_rect.topleft, outer_rect.bottomleft, 1)
        pygame.draw.line(self.screen, (18, 54, 28), outer_rect.topright, outer_rect.bottomright, 1)

    def _draw_piece_at(self, x, y, piece_color, x_scale=1.0, y_scale=1.0, lift_px=0, edge_t=0.0):
        """Draw a disc at board position (x,y) with optional scale for animations.
        x_scale/y_scale squish for flip/drop. lift_px raises centre.
        edge_t (0..1) darkens the face toward its edge-tone for side-on flip depth."""
        cx = x * self.cell_size + self.cell_size // 2
        cy = self.board_top + y * self.cell_size + self.cell_size // 2 - lift_px
        r = int(self.cell_size * 0.38)
        rx = max(1, int(r * x_scale))
        ry = max(1, int(r * y_scale))

        if piece_color == spaceState.BLACK:
            rim_color = (18, 18, 18)
            face_fill = (38, 38, 38)
            edge_fill = (10, 10, 10)
        else:
            rim_color = (190, 190, 190)
            face_fill = (235, 235, 235)
            edge_fill = (155, 155, 155)

        fill_color = self._lerp_color(face_fill, edge_fill, edge_t)

        if x_scale >= 0.98 and y_scale >= 0.98:
            # Full-size — use crisp circles + shadow
            shadow_offset = max(2, self.cell_size // 18)
            shadow_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (0, 0, 0, 80), (r + 2, r + 2), r)
            self.screen.blit(shadow_surf, (cx - r - 2 + shadow_offset, cy - r - 2 + shadow_offset))
            pygame.draw.circle(self.screen, rim_color, (cx, cy), r)
            pygame.draw.circle(self.screen, fill_color, (cx, cy), r - 2)
        else:
            # Scaled — use ellipses (no shadow to avoid smearing)
            pygame.draw.ellipse(self.screen, rim_color,
                                (cx - rx, cy - ry, rx * 2, ry * 2))
            inner_rx = max(1, rx - 2)
            inner_ry = max(1, ry - 2)
            pygame.draw.ellipse(self.screen, fill_color,
                                (cx - inner_rx, cy - inner_ry, inner_rx * 2, inner_ry * 2))

    def _queue_animations(self, result):
        """Build the drop + staggered flip animation list from a play_turn result."""
        now = pygame.time.get_ticks()
        px, py      = result['placed']
        mover_color = result['mover_color']
        flipped     = result.get('flipped', []) or []
        opponent    = spaceState.WHITE if mover_color == spaceState.BLACK else spaceState.BLACK

        # Placed piece drops in
        self._animations.append({
            'type': 'drop', 'x': px, 'y': py,
            'color': mover_color,
            'start': now, 'delay': 0, 'duration': 160,
        })
        # Each flipped piece gets a coin-flip, staggered after the drop
        for i, (fx, fy) in enumerate(flipped):
            self._animations.append({
                'type': 'flip', 'x': fx, 'y': fy,
                'from_color': opponent, 'to_color': mover_color,
                'start': now, 'delay': 140 + i * 50, 'duration': 260,
            })

    def _animations_active(self):
        return bool(self._animations)

    def _update_animations(self):
        """Remove finished animations from the queue."""
        now = pygame.time.get_ticks()
        self._animations = [
            a for a in self._animations
            if (now - a['start'] - a['delay']) < a['duration']
        ]

    def _animating_positions(self):
        return {(a['x'], a['y']) for a in self._animations}

    def _draw_move_hint(self, x, y):
        cx = x * self.cell_size + self.cell_size // 2
        cy = self.board_top + y * self.cell_size + self.cell_size // 2
        hint_r = max(4, int(self.cell_size * 0.1))
        pygame.draw.circle(self.screen, (206, 232, 179), (cx, cy), hint_r)
        pygame.draw.circle(self.screen, (130, 162, 104), (cx, cy), hint_r, 1)

    def _draw_top_bar(self):
        self._top_buttons = []
        bar = pygame.Rect(0, 0, self.width, self.top_bar_height)
        self._draw_vertical_gradient(bar, (44, 44, 52), (30, 30, 36))
        pygame.draw.line(self.screen, (82, 82, 95), (0, self.top_bar_height - 1), (self.width, self.top_bar_height - 1), 1)

        label = self.font.render('Othello', True, (214, 214, 226))
        self.screen.blit(label, (12, 10))

        btn_w = 108
        btn_h = 34
        gap = 10
        y = 10
        reset_rect = pygame.Rect(self.width - btn_w - 12, y, btn_w, btn_h)
        menu_rect = pygame.Rect(reset_rect.left - btn_w - gap, y, btn_w, btn_h)

        mouse_pos = pygame.mouse.get_pos()
        for rect, label_txt, action in (
            (menu_rect, 'Menu', self._go_to_menu),
            (reset_rect, 'Reset', self._reset_game),
        ):
            hovered = rect.collidepoint(mouse_pos)
            bg = (70, 70, 85) if hovered else (56, 56, 68)
            self._draw_rounded_rect(rect, bg, radius=9, border_color=(108, 108, 128), border_width=1)
            txt = self.font.render(label_txt, True, (228, 228, 238))
            self.screen.blit(txt, txt.get_rect(center=rect.center))
            self._top_buttons.append((rect, action))

    def _go_to_menu(self):
        self._animations = []
        self.game_over = False
        self.game_over_text = ''
        self._game_over_buttons = []
        self.in_menu = True

    def _reset_game(self):
        self.setup_game()

    def _handle_top_bar_click(self, pos):
        if pos[1] >= self.top_bar_height:
            return False
        for rect, action in self._top_buttons:
            if rect.collidepoint(pos):
                action()
                return True
        return True

    def _update_game_over_state(self):
        if self.in_menu or self._animations_active():
            return
        if self.game.check_game_over():
            if not self.game_over:
                winner = self.game.get_winner()
                if winner is None:
                    self.game_over_text = 'Tie game.'
                elif winner.color == spaceState.BLACK:
                    self.game_over_text = 'Black wins.'
                else:
                    self.game_over_text = 'White wins.'
                self.game_over = True
        else:
            self.game_over = False
            self.game_over_text = ''

    def _draw_game_over_modal(self):
        if not self.game_over:
            self._game_over_buttons = []
            return

        self._game_over_buttons = []
        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 120))
        self.screen.blit(shade, (0, 0))

        modal_w, modal_h = min(520, self.width - 40), 220
        modal_x = (self.width - modal_w) // 2
        modal_y = self.board_top + (self.size * self.cell_size - modal_h) // 2
        rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
        self._draw_rounded_rect(rect, (34, 34, 44), radius=14, border_color=(78, 78, 98), border_width=1)

        title_font = pygame.font.SysFont(None, 48)
        t1 = title_font.render('Game Over', True, (233, 233, 242))
        self.screen.blit(t1, t1.get_rect(centerx=rect.centerx, top=rect.top + 22))
        t2 = self.font.render(self.game_over_text, True, (206, 206, 218))
        self.screen.blit(t2, t2.get_rect(centerx=rect.centerx, top=rect.top + 80))

        btn_w, btn_h = 180, 42
        gap = 16
        total_w = btn_w * 2 + gap
        start_x = rect.centerx - total_w // 2
        y = rect.bottom - 62
        play_rect = pygame.Rect(start_x, y, btn_w, btn_h)
        menu_rect = pygame.Rect(start_x + btn_w + gap, y, btn_w, btn_h)

        mouse_pos = pygame.mouse.get_pos()
        for button_rect, label_txt, action in (
            (play_rect, 'Play Again', self._reset_game),
            (menu_rect, 'Back to Menu', self._go_to_menu),
        ):
            hovered = button_rect.collidepoint(mouse_pos)
            bg = (56, 136, 84) if hovered else (46, 114, 70)
            self._draw_rounded_rect(button_rect, bg, radius=10, border_color=(98, 188, 128), border_width=1)
            txt = self.font.render(label_txt, True, (232, 248, 236))
            self.screen.blit(txt, txt.get_rect(center=button_rect.center))
            self._game_over_buttons.append((button_rect, action))

    def _handle_game_over_click(self, pos):
        if not self.game_over:
            return False
        for rect, action in self._game_over_buttons:
            if rect.collidepoint(pos):
                action()
                return True
        return True

    def _draw_rounded_rect(self, rect, color, radius=10, border_color=None, border_width=1):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        if border_color:
            pygame.draw.rect(self.screen, border_color, rect, border_width, border_radius=radius)

    def _draw_menu_button(self, rect, label, active=False, hovered=False, font=None):
        if active:
            bg, border, fg = (55, 140, 85), (100, 200, 130), (230, 255, 235)
        elif hovered:
            bg, border, fg = (65, 65, 78), (130, 130, 155), (240, 240, 250)
        else:
            bg, border, fg = (46, 46, 58), (80, 80, 100), (185, 185, 200)
        self._draw_rounded_rect(rect, bg, radius=8, border_color=border, border_width=1)
        f = font or self.font
        surf = f.render(label, True, fg)
        # Clip text to the button rect so it can never overflow
        text_rect = surf.get_rect(center=rect.center)
        self.screen.set_clip(rect)
        self.screen.blit(surf, text_rect)
        self.screen.set_clip(None)

    def handle_menu_click(self, pos):
        mx, my = pos
        for rect, action in getattr(self, '_menu_buttons', []):
            if rect.collidepoint(mx, my):
                action()
                return

    def draw_menu(self):
        self._menu_buttons = []
        mouse_pos = pygame.mouse.get_pos()

        # Background
        self._draw_vertical_gradient(
            pygame.Rect(0, 0, self.width, self.height),
            (22, 22, 30), (12, 12, 20)
        )

        # Card
        card_w, card_h = min(480, self.width - 40), 420
        card_x = (self.width - card_w) // 2
        card_y = (self.height - card_h) // 2
        card = pygame.Rect(card_x, card_y, card_w, card_h)
        self._draw_rounded_rect(card, (32, 32, 44), radius=16, border_color=(60, 60, 80), border_width=1)

        title_font = pygame.font.SysFont(None, 68)
        sub_font = pygame.font.SysFont(None, 30)

        # Title
        title_surf = title_font.render('Othello', True, (220, 220, 235))
        self.screen.blit(title_surf, title_surf.get_rect(centerx=self.width // 2, top=card_y + 18))

        divider_y = card_y + 62
        pygame.draw.line(self.screen, (55, 55, 72), (card_x + 16, divider_y), (card_x + card_w - 16, divider_y), 1)

        row_y = card_y + 80
        col_label = card_x + 18
        col_btn1 = card_x + card_w // 2 - 8
        btn_w, btn_h = 96, 42

        for player_label, attr in [('Black', 'black_mode'), ('White', 'white_mode')]:
            lbl = sub_font.render(player_label, True, (160, 160, 178))
            self.screen.blit(lbl, (col_label, row_y + 10))
            for i, option in enumerate(['Human', 'AI']):
                bx = col_btn1 + i * (btn_w + 10)
                r = pygame.Rect(bx, row_y, btn_w, btn_h)
                active = getattr(self, attr) == option
                self._draw_menu_button(r, option, active=active,
                                       hovered=(not active and r.collidepoint(mouse_pos)),
                                       font=sub_font)
                def _make_setter(a, v):
                    return lambda: setattr(self, a, v)
                self._menu_buttons.append((r, _make_setter(attr, option)))
            row_y += 60

        # Difficulty
        lbl = sub_font.render('Difficulty', True, (160, 160, 178))
        self.screen.blit(lbl, (col_label, row_y + 10))
        diff_btn_w = 56
        diff_start_x = col_btn1
        for i, d in enumerate([1, 2, 3]):
            r = pygame.Rect(diff_start_x + i * (diff_btn_w + 10), row_y, diff_btn_w, btn_h)
            active = self.ai_depth == d
            self._draw_menu_button(r, str(d), active=active,
                                   hovered=(not active and r.collidepoint(mouse_pos)),
                                   font=sub_font)
            def _make_depth(val):
                return lambda: setattr(self, 'ai_depth', val)
            self._menu_buttons.append((r, _make_depth(d)))
        row_y += 66

        # Start button
        start_rect = pygame.Rect(card_x + 20, row_y, card_w - 40, 48)
        start_hovered = start_rect.collidepoint(mouse_pos)
        start_bg = (60, 155, 95) if start_hovered else (46, 130, 76)
        self._draw_rounded_rect(start_rect, start_bg, radius=10,
                                border_color=(100, 200, 130), border_width=1)
        start_lbl = sub_font.render('Start Game', True, (230, 255, 235))
        self.screen.set_clip(start_rect)
        self.screen.blit(start_lbl, start_lbl.get_rect(center=start_rect.center))
        self.screen.set_clip(None)
        self._menu_buttons.append((start_rect, self.setup_game))

    def setup_game(self):
        # Configure players similar to the Tk UI
        ai_depth = int(self.ai_depth)
        from Player import Player
        from AI import AI

        if self.black_mode == 'AI':
            black_player = AI(spaceState.BLACK, depth=ai_depth)
        else:
            black_player = Player(spaceState.BLACK, mode='human')

        if self.white_mode == 'AI':
            white_player = AI(spaceState.WHITE, depth=ai_depth)
        else:
            white_player = Player(spaceState.WHITE, mode='human')

        self.game.reset(player1=black_player, player2=white_player)
        self._animations = []
        self.game_over = False
        self.game_over_text = ''
        self._game_over_buttons = []
        self.in_menu = False

    def draw_board(self):
        board_px = self.size * self.cell_size
        board_bottom = self.board_top + board_px
        self._draw_vertical_gradient(pygame.Rect(0, 0, self.width, self.height), (52, 36, 22), (30, 20, 12))
        self._draw_top_bar()

        frame_outer = pygame.Rect(14, self.board_top + 14, board_px - 28, board_px - 28)
        frame_inner = frame_outer.inflate(-16, -16)
        self._draw_vertical_gradient(frame_outer, (129, 89, 49), (83, 52, 28))
        pygame.draw.rect(self.screen, (158, 116, 67), frame_outer, 2)
        self._draw_vertical_gradient(frame_inner, (44, 118, 58), (22, 76, 38))

        for y in range(self.size):
            for x in range(self.size):
                self._draw_cell(x, y)

        # Static pieces — skip positions currently mid-animation
        animating = self._animating_positions()
        for y in range(self.size):
            for x in range(self.size):
                if (x, y) in animating:
                    continue
                cell = self.game.board.board[y][x]
                if cell == spaceState.EMPTY:
                    continue
                self._draw_piece_at(x, y, cell)

        # Animated pieces overlaid on top
        now = pygame.time.get_ticks()
        piece_r = int(self.cell_size * 0.38)
        for anim in list(self._animations):
            elapsed = now - anim['start'] - anim['delay']
            if elapsed < 0:
                # Delay not yet reached — hold the pre-animation appearance
                if anim['type'] == 'flip':
                    self._draw_piece_at(anim['x'], anim['y'], anim['from_color'])
                # drop: piece not visible yet
                continue
            t = min(1.0, elapsed / anim['duration'])
            if anim['type'] == 'drop':
                scale = 1.0 - (1.0 - t) ** 2   # ease-out quad
                self._draw_piece_at(anim['x'], anim['y'], anim['color'],
                                    x_scale=scale, y_scale=scale)
            elif anim['type'] == 'flip':
                edge_t = math.sin(t * math.pi)
                y_scale = 1.0 - 0.20 * edge_t
                lift_px = int(piece_r * 0.25 * edge_t)
                if t < 0.5:
                    xs = max(0.01, 1.0 - t * 2.0)
                    self._draw_piece_at(
                        anim['x'], anim['y'], anim['from_color'],
                        x_scale=xs, y_scale=y_scale, lift_px=lift_px, edge_t=edge_t
                    )
                else:
                    xs = max(0.01, (t - 0.5) * 2.0)
                    self._draw_piece_at(
                        anim['x'], anim['y'], anim['to_color'],
                        x_scale=xs, y_scale=y_scale, lift_px=lift_px, edge_t=edge_t
                    )

        # Highlight possible moves
        try:
            moves = self.game.current_player.getPossibleMoves(self.game.board)
        except Exception:
            moves = []
        for (mx, my) in moves:
            self._draw_move_hint(mx, my)

        # Status and scores area
        black_score = self.game.player1.calculateScore(self.game.board)
        white_score = self.game.player2.calculateScore(self.game.board)
        status = f'Current: {"Black" if self.game.current_player.color==spaceState.BLACK else "White"}   Black: {black_score} White: {white_score}'
        surf = self.font.render(status, True, (234, 232, 226))
        panel_rect = pygame.Rect(0, board_bottom, self.width, self.window_margin)
        self._draw_vertical_gradient(panel_rect, (34, 34, 34), (20, 20, 20))
        pygame.draw.line(self.screen, (66, 66, 66), (0, board_bottom), (self.width, board_bottom), 2)
        self.screen.blit(surf, (12, board_bottom + 12))

        self._update_game_over_state()
        self._draw_game_over_modal()

    def handle_click(self, pos):
        x_pix, y_pix = pos
        if self._handle_top_bar_click(pos):
            return
        if self._handle_game_over_click(pos):
            return
        if y_pix < self.board_top:
            return
        if y_pix >= self.board_top + self.size * self.cell_size:
            return
        x = x_pix // self.cell_size
        y = (y_pix - self.board_top) // self.cell_size
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return

        if getattr(self.game.current_player, 'mode', 'human') != 'human':
            return

        if self._animations_active():
            return

        moves = list(self.game.current_player.getPossibleMoves(self.game.board))
        if (x, y) not in moves:
            return

        result = self.game.play_turn(x, y)
        if not result:
            return
        self._queue_animations(result)

    def ai_move_if_needed(self):
        # If current player is AI, ask it to choose and play a move
        try:
            cp = self.game.current_player
            if self._animations_active():
                return
            if self.game_over:
                return
            if getattr(cp, 'mode', 'human') == 'AI' and not self.game.check_game_over():
                # choose using minimax if available
                move = None
                if hasattr(cp, 'choose_move_minimax'):
                    move = cp.choose_move_minimax(self.game.board, depth=getattr(cp, 'depth', None))
                if move is None and hasattr(cp, 'choose_move'):
                    move = cp.choose_move(self.game.board)
                if move:
                    x, y = move
                    result = self.game.play_turn(x, y)
                    if result:
                        self._queue_animations(result)
        except Exception:
            logger.exception('Error during AI move')

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if self.in_menu:
                        if event.key == pygame.K_b:
                            self.black_mode = 'AI' if self.black_mode == 'Human' else 'Human'
                        elif event.key == pygame.K_w:
                            self.white_mode = 'AI' if self.white_mode == 'Human' else 'Human'
                        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                            self.ai_depth = int({pygame.K_1:1, pygame.K_2:2, pygame.K_3:3}[event.key])
                        elif event.key == pygame.K_s:
                            self.setup_game()
                        elif event.key == pygame.K_q:
                            self.running = False
                    else:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.in_menu:
                        self.handle_menu_click(event.pos)
                    else:
                        self.handle_click(event.pos)

            if self.in_menu:
                self.draw_menu()
            else:
                self._update_animations()
                self.draw_board()
                # allow AI to play when it's their turn
                self.ai_move_if_needed()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
