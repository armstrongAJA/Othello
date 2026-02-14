import sys
import os
import time
# ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Game import Game
from UI import GameUI

# Diagnostic routine to simulate clicks on menu and canvas and record logs

def run_diagnostics():
    game = Game(8)
    ui = GameUI(game)

    def do_menu_clicks():
        try:
            # Find Start button in main_menu_frame children
            for w in ui.main_menu_frame.winfo_children():
                try:
                    if w.winfo_class() == 'Button':
                        # click center
                        w.event_generate('<ButtonPress-1>', x=10, y=10)
                        w.event_generate('<ButtonRelease-1>', x=10, y=10)
                        time.sleep(0.1)
                except Exception:
                    pass
        except Exception:
            pass

    def do_game_clicks():
        try:
            # assume ui.canvas exists
            if not hasattr(ui, 'canvas'):
                return
            w = ui.canvas
            # click near center of first legal move if available
            moves = list(ui.game.current_player.getPossibleMoves(ui.game.board))
            coords = []
            if moves:
                mx, my = moves[0]
                cx = mx * ui.cell_size + ui.cell_size // 2
                cy = my * ui.cell_size + ui.cell_size // 2
                coords.append((cx, cy))
            # boundary clicks near cell edges
            coords.append((ui.cell_size - 2, ui.cell_size - 2))
            coords.append((ui.size * ui.cell_size - 5, ui.size * ui.cell_size - 5))

            for (x, y) in coords:
                w.event_generate('<ButtonPress-1>', x=int(x), y=int(y))
                w.event_generate('<ButtonRelease-1>', x=int(x), y=int(y))
                time.sleep(0.05)
        except Exception:
            pass

    def during_ai_clicks():
        try:
            # start a move where AI will think; set both players AI to force thinking
            ui.black_mode.set('AI')
            ui.white_mode.set('AI')
            # set AI depth high if variable exists
            try:
                if getattr(ui, 'ai_level_var', None) is not None:
                    ui.ai_level_var.set(3)
            except Exception:
                pass
            # start game to trigger AI
            ui._start_game_clicked()
            time.sleep(0.2)
            # while AI is thinking, rapidly click canvas center
            if hasattr(ui, 'canvas'):
                cx = ui.cell_size * ui.size // 2
                cy = cx
                for i in range(10):
                    ui.canvas.event_generate('<ButtonPress-1>', x=cx, y=cy)
                    ui.canvas.event_generate('<ButtonRelease-1>', x=cx, y=cy)
                    time.sleep(0.05)
        except Exception:
            pass

    # Schedule actions on the UI thread
    ui.root.after(500, do_menu_clicks)
    ui.root.after(1500, lambda: ui._start_game_clicked())
    ui.root.after(2000, do_game_clicks)
    ui.root.after(3000, during_ai_clicks)

    ui.run()

if __name__ == '__main__':
    run_diagnostics()
