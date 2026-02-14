import unittest
import os
import sys
import time
from types import SimpleNamespace

# Ensure project root is importable when running tests directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Ensure we can import the UI module
from UI import GameUI
from Game import Game
from tkinter import ttk

# Logs are stored under tests/logs
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
DEBUG_PATH = os.path.join(LOG_DIR, 'othello_ui_debug.log')
EVENT_PATH = os.path.join(LOG_DIR, 'othello_ui.log')

class TestUIDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # remove existing logs
        for p in (DEBUG_PATH, EVENT_PATH):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    def setUp(self):
        # create a small game and UI but do not call mainloop
        self.game = Game(6)
        self.ui = GameUI(self.game, cell_size=40)
        # ensure setup_game has run
        self.ui.setup_game()
        # short pause to let any initial writes complete
        time.sleep(0.05)

    def tearDown(self):
        try:
            self.ui.root.destroy()
        except Exception:
            pass

    def test_comboboxes_used(self):
        # expect ttk.Combobox instances for black/white selectors
        self.assertIsInstance(self.ui.black_menu, ttk.Combobox)
        self.assertIsInstance(self.ui.white_menu, ttk.Combobox)

    def test_canvas_press_logs_debug(self):
        # simulate a press event object
        evt = SimpleNamespace(x=30, y=30, widget=self.ui.canvas, x_root=self.ui.canvas.winfo_rootx()+30, y_root=self.ui.canvas.winfo_rooty()+30)
        self.ui._on_canvas_press(evt)
        # allow file write
        time.sleep(0.05)
        # check event or debug log for CANVAS PRESS entries
        txt = ''
        if os.path.exists(EVENT_PATH):
            with open(EVENT_PATH, 'r') as f:
                txt += f.read()
        if os.path.exists(DEBUG_PATH):
            with open(DEBUG_PATH, 'r') as f:
                txt += f.read()
        self.assertIn('CANVAS PRESS', txt)

    def test_canvas_release_logs_and_on_click(self):
        evt = SimpleNamespace(x=30, y=30, widget=self.ui.canvas, x_root=self.ui.canvas.winfo_rootx()+30, y_root=self.ui.canvas.winfo_rooty()+30)
        self.ui._on_canvas_release(evt)
        time.sleep(0.05)
        # check event or debug log for CANVAS RELEASE entries
        dbg = ''
        if os.path.exists(EVENT_PATH):
            with open(EVENT_PATH, 'r') as f:
                dbg += f.read()
        if os.path.exists(DEBUG_PATH):
            with open(DEBUG_PATH, 'r') as f:
                dbg += f.read()
        self.assertIn('CANVAS RELEASE', dbg)

if __name__ == '__main__':
    unittest.main()
