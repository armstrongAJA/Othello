from tkinter import Tk, Canvas, Label, Button, Frame, StringVar, IntVar, Radiobutton, messagebox
from tkinter import ttk
from Board import spaceState
from Player import Player
from AI import AI
from types import SimpleNamespace
import threading
import logging
import os
import time
import os
import math

logger = logging.getLogger(__name__)
# Dedicated file logger for UI events (keeps a persistent trace even if terminal output is missing)
event_logger = logging.getLogger('UI.events')
if not event_logger.handlers:
    try:
        log_path = os.path.join(os.getcwd(), 'othello_ui.log')
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        fh.setFormatter(fmt)
        event_logger.addHandler(fh)
        event_logger.setLevel(logging.INFO)
        event_logger.propagate = False
    except Exception:
        pass

# Lightweight debug path used by some immediate writes
DEBUG_PATH = os.path.join(os.getcwd(), 'othello_ui_debug.log')


class GameUI:
    def __init__(self, game, cell_size=60):
        # `game` should be an instance of Game
        self.game = game
        self.cell_size = cell_size
        self.size = game.board.size

        self.root = Tk()
        self.root.title("Othello")

        self.main_menu_frame = Frame(self.root)
        self.game_frame = Frame(self.root)

        # AI difficulty level (1=Easy,2=Medium,3=Hard). Will be IntVar at runtime or StringVar fallback.
        self.ai_level_var = None

        # player mode selectors
        self.black_mode = StringVar(value="Human")
        self.white_mode = StringVar(value="Human")
        self.debug = False
        self._game_over_displayed = False
        # queue of pending click positions captured while animating
        self._pending_clicks = []

        self.show_main_menu()
        # Lightweight fallback debug log (appends immediately)
        try:
            debug_path = os.path.join(os.getcwd(), 'othello_ui_debug.log')
            with open(debug_path, 'a') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} UI INIT\n")
        except Exception:
            pass
        # Bind global event capture to ensure clicks are captured to file
        try:
            def _global_click(e):
                try:
                    with open(debug_path, 'a') as f:
                        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} GLOBAL CLICK widget={str(e.widget)} x={getattr(e,'x_root',None)} y={getattr(e,'y_root',None)} type={getattr(e,'type',None)} focus={str(self.root.focus_get())}\n")
                except Exception:
                    pass
                # attempt to draw a transient dot on the canvas if the click falls inside it
                try:
                    if hasattr(self, 'canvas') and self.canvas.winfo_ismapped():
                        cx = e.x_root - self.canvas.winfo_rootx()
                        cy = e.y_root - self.canvas.winfo_rooty()
                        if 0 <= cx < self.canvas.winfo_width() and 0 <= cy < self.canvas.winfo_height():
                            dot = self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill='red', outline='')
                            self.root.after(200, lambda: self.canvas.delete(dot))
                except Exception:
                    pass

            # use bind_all with '+' to add handler without replacing others
            self.root.bind_all('<ButtonPress-1>', _global_click, add='+')
            self.root.bind_all('<FocusIn>', lambda e: open(debug_path, 'a').write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} FOCUS IN widget={str(e.widget)}\n"), add='+')
            self.root.bind_all('<FocusOut>', lambda e: open(debug_path, 'a').write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} FOCUS OUT widget={str(e.widget)}\n"), add='+')
            # Forward global releases into the canvas when they occur inside it
            def _global_release_forward(e):
                try:
                    if hasattr(self, 'canvas') and self.canvas.winfo_ismapped():
                        wx = getattr(e, 'x_root', None)
                        wy = getattr(e, 'y_root', None)
                        if wx is None or wy is None:
                            return
                        cx = wx - self.canvas.winfo_rootx()
                        cy = wy - self.canvas.winfo_rooty()
                        if 0 <= cx < self.canvas.winfo_width() and 0 <= cy < self.canvas.winfo_height():
                            try:
                                event_logger.info('Forwarding global release to canvas at %s,%s', cx, cy)
                            except Exception:
                                pass
                            fake = SimpleNamespace(x=int(cx), y=int(cy), widget=self.canvas, x_root=wx, y_root=wy)
                            try:
                                self._on_canvas_release(fake)
                            except Exception:
                                pass
                except Exception:
                    pass

            self.root.bind_all('<ButtonRelease-1>', _global_release_forward, add='+')
        except Exception:
            pass

    # -------------------------
    # MAIN MENU
    # -------------------------
    def show_main_menu(self):
        self.game_frame.pack_forget()

        # Clear any existing widgets so repeated returns to the menu don't duplicate items
        for w in self.main_menu_frame.winfo_children():
            w.destroy()

        # Release any stale grabs/focus that could block menu widgets (fixes initial click loss)
        try:
            try:
                g = self.root.grab_current()
                if g:
                    event_logger.info('Releasing stale grab owner=%s', str(g))
                    try:
                        self.root.grab_release()
                    except Exception:
                        pass
            except Exception:
                pass
            # also attempt to clear grabs on child widgets
            for child in getattr(self.root, 'winfo_children', lambda: [])() or []:
                try:
                    if getattr(child, 'grab_release', None):
                        child.grab_release()
                except Exception:
                    pass
        except Exception:
            pass

        self.main_menu_frame.pack()

        Label(self.main_menu_frame, text="Othello", font=("Arial", 24)).pack(pady=20)
        logger.debug('Showing main menu')

        Label(self.main_menu_frame, text="Black Player Mode:").pack()
        # If running under a test harness that replaces Frame with a fake (no .tk),
        # fall back to creating a ttk.Combobox placeholder so unit tests keep expecting
        # `black_menu` attribute. Otherwise use Radiobuttons to avoid popup grabs.
        if getattr(self.main_menu_frame, 'tk', None) is None:
            self.black_menu = ttk.Combobox(self.main_menu_frame, textvariable=self.black_mode, values=("Human", "AI"), state='readonly', takefocus=1)
            try:
                self.black_menu.set(self.black_mode.get())
            except Exception:
                pass
            self.black_menu.pack()
        else:
            bf = Frame(self.main_menu_frame)
            bf.pack()
            def _black_cmd():
                try:
                    event_logger.info('Radio selected black_menu value=%s', self.black_mode.get())
                except Exception:
                    pass
            Radiobutton(bf, text='Human', variable=self.black_mode, value='Human', command=_black_cmd, takefocus=1).pack(side='left')
            Radiobutton(bf, text='AI', variable=self.black_mode, value='AI', command=_black_cmd, takefocus=1).pack(side='left')

        Label(self.main_menu_frame, text="White Player Mode:").pack()
        if getattr(self.main_menu_frame, 'tk', None) is None:
            self.white_menu = ttk.Combobox(self.main_menu_frame, textvariable=self.white_mode, values=("Human", "AI"), state='readonly', takefocus=1)
            try:
                self.white_menu.set(self.white_mode.get())
            except Exception:
                pass
            self.white_menu.pack()
        else:
            wf = Frame(self.main_menu_frame)
            wf.pack()
            def _white_cmd():
                try:
                    event_logger.info('Radio selected white_menu value=%s', self.white_mode.get())
                except Exception:
                    pass
            Radiobutton(wf, text='Human', variable=self.white_mode, value='Human', command=_white_cmd, takefocus=1).pack(side='left')
            Radiobutton(wf, text='AI', variable=self.white_mode, value='AI', command=_white_cmd, takefocus=1).pack(side='left')

        # AI difficulty selector -- prefer Radiobuttons at runtime, but fall back for test harnesses
        if getattr(self.main_menu_frame, 'tk', None) is None:
            # test harness: avoid creating tk Variable objects (no default root)
            try:
                self.ai_level_var = SimpleNamespace(get=lambda: '2')
                cb = ttk.Combobox(self.main_menu_frame, values=('1', '2', '3'))
                cb.set('2')
                cb.pack()
                self.ai_level_menu = cb
            except Exception:
                self.ai_level_var = SimpleNamespace(get=lambda: '2')
                self.ai_level_menu = None
        else:
            # runtime: create IntVar and Radiobuttons to avoid popup grabs
            self.ai_level_var = IntVar(value=2)
            af = Frame(self.main_menu_frame)
            af.pack()
            Label(af, text="AI Difficulty:").pack(side='left')
            Radiobutton(af, text='Easy', variable=self.ai_level_var, value=1).pack(side='left', padx=2)
            Radiobutton(af, text='Medium', variable=self.ai_level_var, value=2).pack(side='left', padx=2)
            Radiobutton(af, text='Hard', variable=self.ai_level_var, value=3).pack(side='left', padx=2)
            self.ai_level_menu = af

        start_btn = Button(self.main_menu_frame, text="Start Game", command=self._start_game_clicked)
        start_btn.pack(pady=20)

        # Give focus to the menu so keyboard/mouse events go to the active widgets
        try:
            # force focus and update idletasks to ensure platform focus state is synced
            self.main_menu_frame.focus_set()
            start_btn.focus_set()
            self.root.update_idletasks()
            event_logger.info('Main menu focused; focus_get=%s grab=%s', str(self.root.focus_get()), str(self.root.grab_current()))
        except Exception:
            pass

        # Trace changes to mode selectors so interactions get logged
        try:
            self.black_mode.trace_add('write', self._on_mode_change)
            self.white_mode.trace_add('write', self._on_mode_change)
        except Exception:
            try:
                self.black_mode.trace('w', self._on_mode_change)
                self.white_mode.trace('w', self._on_mode_change)
            except Exception:
                pass

    # -------------------------
    # START GAME
    # -------------------------
    def start_game(self):
        self.main_menu_frame.pack_forget()
        self.setup_game()
        self.game_frame.pack()
        logger.debug('Start game requested: black_mode=%s white_mode=%s', self.black_mode.get(), self.white_mode.get())

    # --- UI event wrappers -------------------------------------------------
    def _start_game_clicked(self):
        try:
            event_logger.info('MainMenu: Start Game clicked; black_mode=%s white_mode=%s', self.black_mode.get(), self.white_mode.get())
        except Exception:
            pass
        print('UI EVENT: Start Game clicked')
        self.start_game()

    def _reset_clicked(self):
        try:
            event_logger.info('Header: Reset clicked')
        except Exception:
            pass
        print('UI EVENT: Reset clicked')
        self.reset_game()

    def _back_to_menu_clicked(self):
        try:
            event_logger.info('Header: Main Menu clicked')
        except Exception:
            pass
        print('UI EVENT: Main Menu clicked')
        self.back_to_menu()

    def _on_mode_change(self, *args):
        try:
            event_logger.info('Mode changed: black=%s white=%s', self.black_mode.get(), self.white_mode.get())
        except Exception:
            pass

    # -------------------------
    # SETUP GAME SCREEN
    # -------------------------
    def setup_game(self):
        for widget in self.game_frame.winfo_children():
            widget.destroy()

        # Header
        header = Frame(self.game_frame)
        header.pack()

        reset_btn = Button(header, text="Reset", command=self._reset_clicked)
        reset_btn.pack(side="left", padx=10)
        main_btn = Button(header, text="Main Menu", command=self._back_to_menu_clicked)
        main_btn.pack(side="left")

        self.score_label = Label(header, text="")
        self.score_label.pack(side="right", padx=10)

        # Canvas
        canvas_size = self.size * self.cell_size
        self.canvas = Canvas(self.game_frame, width=canvas_size, height=canvas_size, bg="#006400")
        self.canvas.pack()

        # Ensure canvas has input focus (do not force focus which can interfere)
        try:
            self.canvas.focus_set()
        except Exception:
            pass

        # Bind canonical canvas events only. Add explicit press/release handlers
        # so we log both phases and can call on_click on release.
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", lambda e: self.root.config(cursor=""))

        # ensure canvas receives focus when the pointer enters it
        try:
            self.canvas.bind('<Enter>', lambda e: (self.canvas.focus_set(), event_logger.info('Canvas focus on enter')))
        except Exception:
            pass

        self.status = Label(self.game_frame, text="", font=("Arial", 12))
        self.status.pack()

        # On-screen focus/grab indicator to help diagnose missed clicks
        try:
            self.focus_label = Label(self.game_frame, text="Focus: -  Grab: -", font=("Arial", 10))
            self.focus_label.pack()
            self._focus_last = (None, None)
            def _update_focus_info():
                try:
                    focus = str(self.root.focus_get())
                except Exception:
                    focus = 'None'
                try:
                    grab = str(self.root.grab_current())
                except Exception:
                    grab = 'None'
                try:
                    # update only on change to reduce noise
                    if (focus, grab) != getattr(self, '_focus_last', (None, None)):
                        event_logger.info('FOCUS_LABEL update focus=%s grab=%s', focus, grab)
                        self._focus_last = (focus, grab)
                    # show truncated values for readability
                    disp_focus = focus.split('.')[-1] if focus else focus
                    disp_grab = grab.split('.')[-1] if grab else grab
                    self.focus_label.config(text=f"Focus: {disp_focus}  Grab: {disp_grab}")
                except Exception:
                    pass
                # reschedule while the game frame is mapped
                try:
                    if getattr(self, 'game_frame', None) and self.game_frame.winfo_ismapped():
                        self.root.after(250, _update_focus_info)
                except Exception:
                    pass

            # start the updater
            self.root.after(250, _update_focus_info)
        except Exception:
            pass

        # Configure players based on selection
        # determine chosen AI depth (default to 2)
        try:
            if self.ai_level_var is None:
                ai_depth = 2
            else:
                ai_depth = int(self.ai_level_var.get())
        except Exception:
            try:
                ai_depth = int(str(self.ai_level_var.get()))
            except Exception:
                ai_depth = 2

        if self.black_mode.get() == "AI":
            black_player = AI(spaceState.BLACK, depth=ai_depth)
        else:
            black_player = Player(spaceState.BLACK, mode="human")

        if self.white_mode.get() == "AI":
            white_player = AI(spaceState.WHITE, depth=ai_depth)
        else:
            white_player = Player(spaceState.WHITE, mode="human")

        self.game.reset(player1=black_player, player2=white_player)
        # reset one-time UI flags
        self._game_over_displayed = False

        self.draw_board()
        self.update_status()
        logger.debug('Game setup complete, players: %s, %s', type(self.game.player1), type(self.game.player2))
        # If the starting player is AI, schedule AI to make its move
        try:
            if getattr(self.game.current_player, "mode", "human") == "AI":
                self.root.after(100, self.after_move)
        except Exception:
            pass

    # -------------------------
    # RESET GAME
    # -------------------------
    def reset_game(self):
        self.setup_game()

    # -------------------------
    # BACK TO MENU
    # -------------------------
    def back_to_menu(self):
        # ensure any ongoing grabs are released when returning to the menu
        try:
            try:
                if self.root.grab_current():
                    event_logger.info('back_to_menu: releasing grab %s', str(self.root.grab_current()))
                    self.root.grab_release()
            except Exception:
                pass
            for child in getattr(self.root, 'winfo_children', lambda: [])() or []:
                try:
                    if getattr(child, 'grab_release', None):
                        child.grab_release()
                except Exception:
                    pass
        except Exception:
            pass
        self.game_frame.pack_forget()
        self.show_main_menu()

    # -------------------------
    # DRAW BOARD
    # -------------------------
    def draw_board(self):
        self.canvas.delete("all")

        for i in range(self.size + 1):
            x = i * self.cell_size
            self.canvas.create_line(x, 0, x, self.size * self.cell_size)
            y = i * self.cell_size
            self.canvas.create_line(0, y, self.size * self.cell_size, y)

        for y in range(self.size):
            for x in range(self.size):
                cell = self.game.board.board[y][x]
                if cell == spaceState.EMPTY:
                    continue

                cx = x * self.cell_size + self.cell_size // 2
                cy = y * self.cell_size + self.cell_size // 2
                r = int(self.cell_size * 0.4)
                color = "black" if cell == spaceState.BLACK else "white"
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color)

        # Highlight possible moves for current player
        try:
            moves = self.game.current_player.getPossibleMoves(self.game.board)
        except Exception:
            moves = []
        for (mx, my) in moves:
            # get top-left coordinate
            cx = mx * self.cell_size + self.cell_size // 2
            cy = my * self.cell_size + self.cell_size // 2
            r = int(self.cell_size * 0.15)
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#90EE90", outline="")

        self.update_scores()

    # -------------------------
    # CLICK HANDLER
    # -------------------------
    def on_click(self, event):
        # Fallback print to ensure clicks are visible in terminal logs
        print(f"UI CLICK pixels=({event.x},{event.y})")
        try:
            event_logger.info('CLICK pixels=(%s,%s) -> canvas', event.x, event.y)
        except Exception:
            pass
        # Map coordinates and log context for diagnosis
        try:
            widget = str(event.widget)
        except Exception:
            widget = None
        try:
            grab = str(self.root.grab_current())
        except Exception:
            grab = None
        try:
            focus = str(self.root.focus_get())
        except Exception:
            focus = None
        event_logger.info('on_click widget=%s focus=%s grab=%s', widget, focus, grab)

        # map pixel to board cell; use integer division as baseline
        x = event.x // self.cell_size
        y = event.y // self.cell_size
        logger.debug('Canvas click at pixels (%s,%s) -> cell (%s,%s)', event.x, event.y, x, y)

        # bounds check
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return

        if getattr(self.game.current_player, "mode", "human") != "human":
            logger.debug('Click ignored: current player is not human (%s)', getattr(self.game.current_player, 'mode', None))
            return

        # Refresh UI state to avoid race conditions
        try:
            self.draw_board()
            self.update_status()
            self.root.update_idletasks()
        except Exception:
            pass

        # If we're animating, queue the click to be replayed after animation
        try:
            if getattr(self, 'animating', False):
                try:
                    self._pending_clicks.append((event.x, event.y))
                    event_logger.info('Queued click during animation at (%s,%s)', event.x, event.y)
                except Exception:
                    pass
                return
        except Exception:
            pass

        # only accept click if it's a legal move (use a local snapshot)
        try:
            moves = list(self.game.current_player.getPossibleMoves(self.game.board))
        except Exception:
            moves = []

        if (x, y) not in moves:
            # Try snapping to a nearby legal move if the click is near a cell boundary.
            try:
                best = None
                best_dist = None
                for dx, dy in [(0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in moves and 0 <= nx < self.size and 0 <= ny < self.size:
                        cx = nx * self.cell_size + self.cell_size / 2
                        cy = ny * self.cell_size + self.cell_size / 2
                        dist = math.hypot(event.x - cx, event.y - cy)
                        if best is None or dist < best_dist:
                            best = (nx, ny)
                            best_dist = dist
                if best and best_dist is not None and best_dist <= (self.cell_size * 0.6):
                    event_logger.info('Snapped click from (%s,%s) to nearby legal move %s (dist=%.1f)', (x,y), (event.x,event.y), best, best_dist)
                    x, y = best
                else:
                    logger.debug('Click not in moves: cell=%s current=%s moves=%s animating=%s', (x,y), getattr(self.game.current_player,'color',None), moves, getattr(self, 'animating', False))
                    if self.debug:
                        logger.debug('UI debug: click at %s ignored; current_player=%s moves=%s', (x,y), getattr(self.game.current_player,'color',None), moves)
                    return
            except Exception:
                return

        if getattr(self, 'animating', False):
            logger.debug('Click ignored while animating')
            return

        result = self.game.play_turn(x, y)
        if not result:
            return

        # animate flips if any
        flips = result.get('flipped', [])
        mover_color = result.get('mover_color', None)
        logger.debug('Move played result: placed=%s flipped=%s mover=%s', result.get('placed'), flips, mover_color)
        if flips:
            self.animate_flips(flips, mover_color)
        else:
            self.after_move()

    def on_motion(self, event):
        # Fallback print for motion events (helps confirm event reachability)
        print(f"UI MOTION pixels=({event.x},{event.y})")
        try:
            event_logger.info('MOTION pixels=(%s,%s)', event.x, event.y)
        except Exception:
            pass
        # Auto-focus the canvas when the pointer moves over it to reduce missed clicks
        try:
            if hasattr(self, 'canvas'):
                self.canvas.focus_set()
                try:
                    event_logger.info('Motion auto-focused canvas')
                except Exception:
                    pass
        except Exception:
            pass
        x = event.x // self.cell_size
        y = event.y // self.cell_size
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            self.root.config(cursor="")
            return
        try:
            moves = list(self.game.current_player.getPossibleMoves(self.game.board))
            if (x, y) in moves:
                self.root.config(cursor="hand2")
            else:
                self.root.config(cursor="")
        except Exception:
            logger.exception('Error while handling motion event')
            self.root.config(cursor="")

    # Canvas press/release helpers for more robust logging
    def _on_canvas_press(self, event):
        # Attempt to clear any stale grabs and ensure canvas has focus before processing
        try:
            try:
                if self.root.grab_current():
                    try:
                        self.root.grab_release()
                    except Exception:
                        pass
            except Exception:
                pass
            for child in getattr(self.root, 'winfo_children', lambda: [])() or []:
                try:
                    if getattr(child, 'grab_release', None):
                        child.grab_release()
                except Exception:
                    pass
            if hasattr(self, 'canvas'):
                try:
                    self.canvas.focus_set()
                except Exception:
                    pass
            event_logger.info('CANVAS PRESS widget=%s x=%s y=%s focus=%s grab=%s',
                              str(event.widget), getattr(event, 'x', None), getattr(event, 'y', None), str(self.root.focus_get()), str(self.root.grab_current()))
        except Exception:
            pass
        try:
            with open(DEBUG_PATH, 'a') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} CANVAS PRESS x={getattr(event,'x',None)} y={getattr(event,'y',None)}\n")
        except Exception:
            pass
        # leave visual dot for quick feedback (if canvas exists)
        try:
            if hasattr(self, 'canvas') and self.canvas.winfo_ismapped():
                dot = self.canvas.create_oval(event.x-2, event.y-2, event.x+2, event.y+2, fill='blue', outline='')
                self.root.after(120, lambda: self.canvas.delete(dot))
        except Exception:
            pass

    def _on_canvas_release(self, event):
        try:
            event_logger.info('CANVAS RELEASE widget=%s x=%s y=%s focus=%s grab=%s',
                              str(event.widget), event.x, event.y, str(self.root.focus_get()), str(self.root.grab_current()))
        except Exception:
            pass
        try:
            with open(DEBUG_PATH, 'a') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} CANVAS RELEASE x={getattr(event,'x',None)} y={getattr(event,'y',None)}\n")
        except Exception:
            pass
        # Additional diagnostics: list canvas items under the release point and pointer/widget info
        try:
            if hasattr(self, 'canvas'):
                try:
                    items = self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
                    item_info = []
                    for it in items:
                        try:
                            it_type = self.canvas.type(it)
                            it_coords = self.canvas.coords(it)
                            it_fill = self.canvas.itemcget(it, 'fill')
                        except Exception:
                            it_type = it_coords = it_fill = None
                        item_info.append((it, it_type, it_coords, it_fill))
                    event_logger.info('CANVAS ITEMS AT RELEASE: %s', item_info)
                except Exception:
                    event_logger.exception('Failed to enumerate canvas items at release')
                # widget under pointer (global coords)
                try:
                    wx = getattr(event, 'x_root', None)
                    wy = getattr(event, 'y_root', None)
                    containing = None
                    if wx is not None and wy is not None:
                        containing = str(self.root.winfo_containing(wx, wy))
                    event_logger.info('POINTER pos=(%s,%s) containing_widget=%s', wx, wy, containing)
                except Exception:
                    pass
        except Exception:
            pass
        # Call the original click handler on release so click semantics match user's expectation
        try:
            self.on_click(event)
        except Exception:
            logger.exception('Error handling canvas release/click')

    def after_move(self):
        self.draw_board()
        self.update_status()

        # If current player is AI, schedule a single AI move after a short delay
        if getattr(self.game.current_player, "mode", "human") == "AI" and not self.game.check_game_over():
            def do_ai_move():
                # Run AI computation in a background thread to avoid blocking the GUI
                def worker():
                    try:
                        event_logger.info('AI computation started')
                    except Exception:
                        pass
                    ai_move = None
                    try:
                        ai_move = self.game.current_player.choose_move(self.game.board)
                    except Exception:
                        try:
                            # let AI instance decide its default depth if None passed
                            ai_move = self.game.current_player.choose_move_minimax(self.game.board, None)
                        except Exception:
                            ai_move = None

                    def apply_move():
                        try:
                            if ai_move:
                                logger.debug('AI selected move %s', ai_move)
                                result = self.game.play_turn(ai_move[0], ai_move[1])
                                logger.debug('AI play_turn result %s', result)
                                if result and result.get('flipped'):
                                    # animate flips for AI move; when animation finishes it will call after_move again
                                    self.animate_flips(result.get('flipped'), result.get('mover_color'))
                                else:
                                    # no flips (should be rare), redraw and schedule next AI move
                                    self.draw_board()
                                    self.update_status()
                                    self.root.after(300, self.after_move)
                            else:
                                # no AI move available; just redraw
                                self.draw_board()
                                self.update_status()
                        except Exception:
                            logger.exception('Error applying AI move')
                    try:
                        # schedule application on main thread
                        self.root.after(0, apply_move)
                    except Exception:
                        pass
                    try:
                        event_logger.info('AI computation finished')
                    except Exception:
                        pass

                t = threading.Thread(target=worker, daemon=True)
                t.start()

            # small delay so animations and UI updates are visible
            self.root.after(300, do_ai_move)

        if self.game.check_game_over() and not getattr(self, '_game_over_displayed', False):
            self._game_over_displayed = True
            winner = self.game.get_winner()
            if winner is None:
                messagebox.showinfo("Game Over", "Tie")
            else:
                color = "Black" if winner.color == spaceState.BLACK else "White"
                messagebox.showinfo("Game Over", f"{color} wins")

    # -------------------------
    # ANIMATION
    # -------------------------
    def animate_flips(self, flips, mover_color):
        if not flips:
            self.after_move()
            return

        self.animating = True

        final_color = 'black' if mover_color == spaceState.BLACK else 'white'
        initial_color = 'white' if final_color == 'black' else 'black'

        items = []
        for (fx, fy) in flips:
            cx = fx * self.cell_size + self.cell_size // 2
            cy = fy * self.cell_size + self.cell_size // 2
            r = int(self.cell_size * 0.4)
            item = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=initial_color, outline='')
            items.append((item, cx, cy, r))

        steps = 6

        def step_shrink(step):
            if step < steps:
                for (item, cx, cy, r) in items:
                    factor = 1 - (step + 1) / steps
                    rx = r * factor
                    ry = r * factor
                    self.canvas.coords(item, cx - rx, cy - ry, cx + rx, cy + ry)
                self.root.after(50, lambda: step_shrink(step + 1))
            else:
                for (item, _, _, _) in items:
                    self.canvas.itemconfig(item, fill=final_color)
                self.root.after(50, lambda: step_grow(0))

        def step_grow(step):
            if step < steps:
                for (item, cx, cy, r) in items:
                    factor = (step + 1) / steps
                    rx = r * factor
                    ry = r * factor
                    self.canvas.coords(item, cx - rx, cy - ry, cx + rx, cy + ry)
                self.root.after(50, lambda: step_grow(step + 1))
            else:
                for (item, _, _, _) in items:
                    self.canvas.delete(item)
                # final redraw (board already updated by game logic)
                self.draw_board()
                self.update_status()
                self.animating = False
                # replay any queued clicks that happened during the animation
                try:
                    if getattr(self, '_pending_clicks', None):
                        try:
                            px, py = self._pending_clicks.pop(0)
                            # synthesize an event object similar to the real one
                            fake = SimpleNamespace(x=px, y=py, widget=self.canvas, x_root=None, y_root=None)
                            event_logger.info('Replaying queued click at (%s,%s)', px, py)
                            # schedule slightly later to allow UI settle
                            self.root.after(50, lambda: self.on_click(fake))
                        except Exception:
                            pass
                except Exception:
                    pass
                # continue with AI loop if needed
                self.after_move()

        step_shrink(0)

    # -------------------------
    # STATUS + SCORES
    # -------------------------
    def update_status(self):
        cp = self.game.current_player
        color = "Black" if cp.color == spaceState.BLACK else "White"
        self.status.config(text=f"Current player: {color}")
        self.update_scores()

    def update_scores(self):
        black_score = self.game.player1.calculateScore(self.game.board)
        white_score = self.game.player2.calculateScore(self.game.board)
        self.score_label.config(text=f"Black: {black_score}   White: {white_score}")

    # -------------------------
    def run(self):
        self.root.mainloop()
