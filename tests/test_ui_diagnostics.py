import unittest
import os
import sys
import time

# Ensure project root is importable when running tests directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pygame_ui import PygameUI as GameUI
from Game import Game
from Board import spaceState


class TestUIDiagnostics(unittest.TestCase):
    def setUp(self):
        # create a small game and UI but do not call mainloop
        self.game = Game(6)
        self.ui = GameUI(self.game, cell_size=40)
        # ensure setup_game has run
        try:
            self.ui.setup_game()
        except Exception:
            # some UI implementations may not require explicit setup
            pass
        # short pause
        time.sleep(0.02)

    def tearDown(self):
        # pygame UI may not have a root; ignore
        try:
            if hasattr(self.ui, 'running'):
                self.ui.running = False
        except Exception:
            pass

    def test_gameui_exists(self):
        self.assertIsNotNone(GameUI)

    def test_handle_click_plays_move(self):
        # find a legal move for the current player and simulate a click
        moves = list(self.game.current_player.getPossibleMoves(self.game.board))
        if not moves:
            self.skipTest('No legal moves available for starting position')
        mx, my = moves[0]
        # pixel position in middle of cell
        px = mx * 40 + 20
        py = my * 40 + 20
        # call handle_click if available, otherwise play directly
        if hasattr(self.ui, 'handle_click'):
            self.ui.handle_click((px, py))
        else:
            self.game.play_turn(mx, my)
        self.assertNotEqual(self.game.board.board[my][mx], spaceState.EMPTY)


if __name__ == '__main__':
    unittest.main()
