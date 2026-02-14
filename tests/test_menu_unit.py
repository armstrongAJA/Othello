import unittest
import types
import importlib

# Import UI module
import UI

class DummyWidget:
    def __init__(self, parent=None, *args, **kwargs):
        self.parent = parent
        self._children = []
        self.bound = {}
    def pack(self, *args, **kwargs):
        if hasattr(self.parent, '_children'):
            self.parent._children.append(self)
    def pack_forget(self):
        pass
    def destroy(self):
        pass
    def winfo_children(self):
        return list(self._children)
    def bind(self, event, cb=None, **kwargs):
        self.bound[event] = cb
    def config(self, **kwargs):
        pass
    def focus_set(self):
        pass

class DummyCombobox(DummyWidget):
    def __init__(self, parent=None, textvariable=None, values=None, state=None, takefocus=None):
        super().__init__(parent)
        self._value = None
        self.textvariable = textvariable
    def set(self, v):
        self._value = v

class DummyButton(DummyWidget):
    def __init__(self, parent=None, text=None, command=None):
        super().__init__(parent)
        self.command = command
    def invoke(self):
        if self.command:
            self.command()

class FakeFrame(DummyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._children = []

class FakeRoot:
    def __init__(self):
        self._children = []
    def bind_all(self, *args, **kwargs):
        pass
    def focus_get(self):
        return None

class TestMenuUI(unittest.TestCase):
    def setUp(self):
        # Monkeypatch UI widgets to dummy ones
        self._orig_Button = UI.Button
        self._orig_Label = UI.Label
        self._orig_Frame = UI.Frame
        self._orig_Combobox = UI.ttk.Combobox

        UI.Button = lambda parent, **kwargs: DummyButton(parent, **kwargs)
        UI.Label = lambda parent, **kwargs: DummyWidget(parent, **kwargs)
        UI.Frame = lambda parent=None: FakeFrame(parent)
        UI.ttk.Combobox = lambda parent, **kwargs: DummyCombobox(parent, **kwargs)

        # Create an instance without running __init__
        self.ui = UI.GameUI.__new__(UI.GameUI)
        # minimal attributes
        self.ui.root = FakeRoot()
        self.ui.main_menu_frame = FakeFrame(self.ui.root)
        self.ui.game_frame = FakeFrame(self.ui.root)
        # simple string-like objects with get()
        self.ui.black_mode = types.SimpleNamespace(get=lambda: 'Human')
        self.ui.white_mode = types.SimpleNamespace(get=lambda: 'Human')
        self.ui.debug = False

    def tearDown(self):
        # restore
        UI.Button = self._orig_Button
        UI.Label = self._orig_Label
        UI.Frame = self._orig_Frame
        UI.ttk.Combobox = self._orig_Combobox

    def test_show_main_menu_creates_widgets(self):
        # Call the method
        self.ui.show_main_menu()
        # Ensure combobox attributes created
        self.assertTrue(hasattr(self.ui, 'black_menu'))
        self.assertTrue(hasattr(self.ui, 'white_menu'))
        self.assertIsInstance(self.ui.black_menu, DummyCombobox)
        self.assertIsInstance(self.ui.white_menu, DummyCombobox)
        # main menu frame should have children (labels/buttons added)
        children = self.ui.main_menu_frame.winfo_children()
        self.assertTrue(len(children) >= 1)

    def test_start_button_invokes_start(self):
        # Replace start_game with a spy
        called = {'v': False}
        def spy_start():
            called['v'] = True
        self.ui.start_game = spy_start
        self.ui.show_main_menu()
        # find the start button in children (last packed)
        children = self.ui.main_menu_frame._children
        # find DummyButton
        btns = [c for c in children if isinstance(c, DummyButton)]
        self.assertTrue(len(btns) >= 1)
        # invoke
        btns[-1].invoke()
        self.assertTrue(called['v'])

if __name__ == '__main__':
    unittest.main()
