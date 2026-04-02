"""Compatibility shim: expose a `GameUI` backed by the pygame UI and
provide lightweight widget stubs so existing tests that monkeypatch
`UI.Button`, `UI.Frame`, `UI.ttk.Combobox`, etc continue to work.

This file intentionally removes any dependency on Tkinter.
"""
from types import SimpleNamespace
import logging

logger = logging.getLogger(__name__)

# Try to import the pygame-backed UI implementation
try:
    from pygame_ui import PygameUI
except Exception:
    PygameUI = None

# Expose GameUI for runtime; prefer PygameUI
GameUI = PygameUI

# Minimal widget stubs (tests may monkeypatch these)
class _StubWidget:
    def __init__(self, *args, **kwargs):
        self._children = []
    def pack(self, *args, **kwargs):
        pass
    def pack_forget(self):
        pass
    def destroy(self):
        pass
    def winfo_children(self):
        return list(self._children)
    def bind(self, *args, **kwargs):
        pass
    def config(self, *args, **kwargs):
        pass
    def focus_set(self):
        pass

# Provide names that tests expect to monkeypatch
Button = _StubWidget
Label = _StubWidget
Frame = _StubWidget
Canvas = _StubWidget
Radiobutton = _StubWidget

# Simple variable-like objects with `get()` used by tests
def StringVar(value=None):
    return SimpleNamespace(get=lambda: value, set=lambda v: None, trace_add=lambda *a, **k: None, trace=lambda *a, **k: None)

def IntVar(value=0):
    return SimpleNamespace(get=lambda: value, set=lambda v: None)

# Lightweight ttk namespace
class _TTK:
    class Combobox(_StubWidget):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self._value = None
        def set(self, v):
            self._value = v

ttk = _TTK()

# Minimal messagebox shim
messagebox = SimpleNamespace(showinfo=lambda *a, **k: None)

# Keep an API compatible placeholder for ui_helpers functions tests might call
def setup_global_bindings(*args, **kwargs):
    return None

__all__ = ['GameUI', 'Button', 'Label', 'Frame', 'Canvas', 'StringVar', 'IntVar', 'Radiobutton', 'messagebox', 'ttk', 'setup_global_bindings']
        try:
