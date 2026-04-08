"""Tests for WintoucherApp keyboard handlers and toggle_listen.

Since WintoucherApp.__init__ is tightly coupled to tkinter, pynput, Win32, and
pystray, we test the handler logic by extracting and calling the methods directly
on a partially-constructed app, bypassing the full __init__.
"""

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest
from pynput.keyboard import Key as SpecialKey
from pynput.keyboard import KeyCode
from pynput.keyboard import Listener

from wintoucher.controller.dots import Dots
from wintoucher.gui.overlay import Overlay
from wintoucher.util.key import Key


@pytest.fixture(autouse=True)
def skip_iconbitmap(monkeypatch):
    monkeypatch.setattr(tk.Toplevel, "iconbitmap", lambda self, *a, **kw: None)


@pytest.fixture
def app_parts(tk_root):
    """Build the parts of WintoucherApp needed for handler testing."""
    dots = Dots()
    overlay = Overlay(
        master=tk_root,
        app_name="Test",
        app_icon="",
        dots=dots,
        update_dot_detail=lambda: None,
    )
    overlay.new_dot_type.set("Press")

    # Build a minimal app-like object with the fields keyboard_handlers needs
    app = MagicMock()
    app.dots = dots
    app.overlay = overlay
    app.keyboard_listening = False
    app.listen_button = tk.ttk.Button(tk_root, text="")
    app.tray_icon = MagicMock()

    # Bind the real toggle_listen method
    from wintoucher import WintoucherApp
    app.toggle_listen = lambda notify=False: WintoucherApp.toggle_listen(app, notify)

    # Bind the real keyboard_handlers method, with a mock keyboard.canonical
    app.keyboard = MagicMock()
    app.keyboard.canonical = lambda key: key
    app.keyboard_handlers = lambda: WintoucherApp.keyboard_handlers(app)

    # Mock touch_manager
    app.touch_manager = MagicMock()

    yield app, dots, overlay
    overlay.destroy()


class TestToggleListen:
    def test_toggle_flips_state(self, app_parts):
        app, _, _ = app_parts
        app.keyboard_listening = False
        app.toggle_listen(False)
        assert app.keyboard_listening is True
        app.toggle_listen(False)
        assert app.keyboard_listening is False

    def test_button_text_updates(self, app_parts):
        app, _, _ = app_parts
        app.keyboard_listening = False
        app.toggle_listen(False)
        assert "Pause" in app.listen_button.cget("text")
        app.toggle_listen(False)
        assert "Resume" in app.listen_button.cget("text")


class TestKeyboardHandlers:
    def test_handlers_can_be_bound_to_pynput_listener(self, app_parts):
        app, _, _ = app_parts
        handlers = app.keyboard_handlers()

        listener = Listener(**handlers)

        assert listener is not None
        listener.stop()

    def test_esc_toggles_listen_when_not_listening(self, app_parts):
        app, _, _ = app_parts
        app.keyboard_listening = False
        handlers = app.keyboard_handlers()
        handlers["on_press"](SpecialKey.esc)
        assert app.keyboard_listening is True

    def test_esc_toggles_listen_when_listening(self, app_parts):
        app, _, _ = app_parts
        app.keyboard_listening = True
        handlers = app.keyboard_handlers()
        handlers["on_press"](SpecialKey.esc)
        assert app.keyboard_listening is False

    def test_non_esc_blocked_when_not_listening(self, app_parts):
        app, dots, overlay = app_parts
        app.keyboard_listening = False
        overlay.hide()
        handlers = app.keyboard_handlers()
        key = KeyCode.from_char("a")
        dots.add("Press", 100, 100)
        dots.dots[0].key = key
        # Should not trigger touch when not listening
        handlers["on_press"](key)
        app.touch_manager.press.assert_not_called()

    def test_key_press_triggers_touch_when_listening(self, app_parts):
        app, dots, overlay = app_parts
        app.keyboard_listening = True
        overlay.hide()  # must be withdrawn for touch injection
        handlers = app.keyboard_handlers()
        key = KeyCode.from_char("a")
        dots.add("Press", 100, 100)
        dots.dots[0].key = key
        handlers["on_press"](key)
        app.touch_manager.press.assert_called_once_with(0, 100, 100)

    def test_key_release_assigns_key_when_overlay_shown(self, app_parts):
        app, dots, overlay = app_parts
        app.keyboard_listening = True
        overlay.show()
        dots.add("Press", 100, 100)
        dots.current_viewed_dot = dots.dots[0]
        handlers = app.keyboard_handlers()
        key = KeyCode.from_char("x")
        handlers["on_release"](key)
        assert dots.dots[0].key == key

    def test_key_release_does_not_assign_when_dot_already_bound(self, app_parts):
        app, dots, overlay = app_parts
        app.keyboard_listening = True
        overlay.show()
        dots.add("Press", 100, 100)
        existing_key = KeyCode.from_char("a")
        dots.dots[0].key = existing_key
        dots.current_viewed_dot = dots.dots[0]
        handlers = app.keyboard_handlers()
        new_key = KeyCode.from_char("x")
        handlers["on_release"](new_key)
        # Should NOT overwrite existing key
        assert dots.dots[0].key == existing_key
