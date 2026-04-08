import tkinter as tk

import pytest


@pytest.fixture
def tk_root():
    """Create and teardown a tkinter root for tests that need it."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
