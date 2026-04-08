import tkinter as tk

import pytest


@pytest.fixture(scope="session")
def tk_root():
    """Create and teardown a tkinter root for tests that need it.

    Session-scoped to avoid tkinter re-initialization issues on Windows where
    creating multiple Tk() instances across tests causes TclError.
    """
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
