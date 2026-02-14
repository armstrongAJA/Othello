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

DEBUG_PATH = os.path.join(os.getcwd(), 'othello_ui_debug.log')
EVENT_PATH = os.path.join(os.getcwd(), 'othello_ui.log')

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
        # check event log for CANVAS PRESS entries
        if os.path.exists(EVENT_PATH):
            with open(EVENT_PATH, 'r') as f:
                txt = f.read()
        else:
            txt = ''
        self.assertIn('CANVAS PRESS', txt)

    def test_canvas_release_logs_and_on_click(self):
        evt = SimpleNamespace(x=30, y=30, widget=self.ui.canvas, x_root=self.ui.canvas.winfo_rootx()+30, y_root=self.ui.canvas.winfo_rooty()+30)
        self.ui._on_canvas_release(evt)
        time.sleep(0.05)
        # both debug and event logs should exist after release -> on_click
        # check event log for CANVAS RELEASE entries
        if os.path.exists(EVENT_PATH):
            with open(EVENT_PATH, 'r') as f:
                dbg = f.read()
        else:
            dbg = ''
        self.assertIn('CANVAS RELEASE', dbg)
        # on_click should have resulted in a CLICK entry in the event log
        self.assertTrue('CLICK' in dbg or 'on_click' in dbg)

if __name__ == '__main__':
    unittest.main()
