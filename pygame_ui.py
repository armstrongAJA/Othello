import os
import sys
import time
import logging
try:
    import pygame
except Exception:
    pygame = None

from Board import spaceState

logger = logging.getLogger(__name__)


class PygameUI:
    def __init__(self, game, cell_size=60):
        if pygame is None:
            raise ImportError('pygame is required for PygameUI')
        self.game = game
        self.cell_size = cell_size
        self.size = game.board.size
        self.window_margin = 100
        self.width = self.size * self.cell_size
        self.height = self.size * self.cell_size + self.window_margin

        pygame.init()
        pygame.display.set_caption('Othello (pygame)')
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)

        # Menu state
        self.black_mode = 'Human'
        self.white_mode = 'Human'
        self.ai_depth = 2
        self.running = True
        self.in_menu = True

    def draw_menu(self):
        self.screen.fill((30, 30, 30))
        title = pygame.font.SysFont(None, 48).render('Othello', True, (240, 240, 240))
        self.screen.blit(title, (20, 10))

        lines = [
            f'Black: {self.black_mode}   (press b to toggle)',
            f'White: {self.white_mode}   (press w to toggle)',
            f'AI difficulty: {self.ai_depth}   (press 1/2/3)',
            'Press S to start the game',
            'Press Q to quit'
        ]
        y = 80
        for ln in lines:
            surf = self.font.render(ln, True, (220, 220, 220))
            self.screen.blit(surf, (20, y))
            y += 32

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
        self.in_menu = False

    def draw_board(self):
        # Board background
        self.screen.fill((0, 100, 0))

        # Grid lines
        for i in range(self.size + 1):
            x = i * self.cell_size
            pygame.draw.line(self.screen, (0, 0, 0), (x, 0), (x, self.size * self.cell_size))
            y = i * self.cell_size
            pygame.draw.line(self.screen, (0, 0, 0), (0, y), (self.size * self.cell_size, y))

        # Pieces
        for y in range(self.size):
            for x in range(self.size):
                cell = self.game.board.board[y][x]
                if cell == spaceState.EMPTY:
                    continue
                cx = x * self.cell_size + self.cell_size // 2
                cy = y * self.cell_size + self.cell_size // 2
                r = int(self.cell_size * 0.4)
                color = (0, 0, 0) if cell == spaceState.BLACK else (255, 255, 255)
                pygame.draw.circle(self.screen, color, (cx, cy), r)

        # Highlight possible moves
        try:
            moves = self.game.current_player.getPossibleMoves(self.game.board)
        except Exception:
            moves = []
        for (mx, my) in moves:
            cx = mx * self.cell_size + self.cell_size // 2
            cy = my * self.cell_size + self.cell_size // 2
            pygame.draw.circle(self.screen, (144, 238, 144), (cx, cy), int(self.cell_size * 0.12))

        # Status and scores area
        black_score = self.game.player1.calculateScore(self.game.board)
        white_score = self.game.player2.calculateScore(self.game.board)
        status = f'Current: {"Black" if self.game.current_player.color==spaceState.BLACK else "White"}   Black: {black_score} White: {white_score}'
        surf = self.font.render(status, True, (240, 240, 240))
        self.screen.fill((40, 40, 40), (0, self.size * self.cell_size, self.width, self.window_margin))
        self.screen.blit(surf, (10, self.size * self.cell_size + 10))

    def handle_click(self, pos):
        x_pix, y_pix = pos
        if y_pix >= self.size * self.cell_size:
            return
        x = x_pix // self.cell_size
        y = y_pix // self.cell_size
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return

        if getattr(self.game.current_player, 'mode', 'human') != 'human':
            return

        moves = list(self.game.current_player.getPossibleMoves(self.game.board))
        if (x, y) not in moves:
            return

        result = self.game.play_turn(x, y)
        if not result:
            return

    def ai_move_if_needed(self):
        # If current player is AI, ask it to choose and play a move
        try:
            cp = self.game.current_player
            if getattr(cp, 'mode', 'human') == 'AI' and not self.game.check_game_over():
                # choose using minimax if available
                move = None
                if hasattr(cp, 'choose_move_minimax'):
                    move = cp.choose_move_minimax(self.game.board, depth=getattr(cp, 'depth', None))
                if move is None and hasattr(cp, 'choose_move'):
                    move = cp.choose_move(self.game.board)
                if move:
                    x, y = move
                    self.game.play_turn(x, y)
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
                        # start game on click anywhere in menu
                        self.setup_game()
                    else:
                        self.handle_click(event.pos)

            if self.in_menu:
                self.draw_menu()
            else:
                self.draw_board()
                # allow AI to play when it's their turn
                self.ai_move_if_needed()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
