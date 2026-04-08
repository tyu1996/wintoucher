import tkinter as tk

import pytest

from wintoucher.controller.dots import Dots
from wintoucher.data.dot import PressDot
from wintoucher.gui.overlay import Overlay


@pytest.fixture
def overlay_setup(tk_root):
    """Create an Overlay with a Dots controller and a mock update callback."""
    dots = Dots()
    detail_calls = []

    def track_detail():
        detail_calls.append(1)

    overlay = Overlay(
        master=tk_root,
        app_name="Test",
        app_icon="",
        dots=dots,
        update_dot_detail=track_detail,
    )
    overlay.new_dot_type.set("Press")
    yield overlay, dots, detail_calls
    overlay.destroy()


@pytest.fixture(autouse=True)
def skip_iconbitmap(monkeypatch):
    """Skip iconbitmap call since test has no .ico file."""
    monkeypatch.setattr(tk.Toplevel, "iconbitmap", lambda self, *a, **kw: None)


class TestOverlayShowHide:
    def test_initial_state_not_showing(self, overlay_setup):
        overlay, _, _ = overlay_setup
        assert overlay.showing is False

    def test_show_sets_showing(self, overlay_setup):
        overlay, _, _ = overlay_setup
        overlay.show()
        assert overlay.showing is True

    def test_hide_clears_showing(self, overlay_setup):
        overlay, _, _ = overlay_setup
        overlay.show()
        overlay.hide()
        assert overlay.showing is False


class TestOverlayGetClosestDot:
    def test_returns_none_when_empty(self, overlay_setup):
        overlay, _, _ = overlay_setup
        assert overlay.get_closest_dot(100, 100) is None

    def test_returns_close_dot(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        result = overlay.get_closest_dot(105, 105)
        assert result is not None
        assert result.x == 100

    def test_returns_none_when_too_far(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        result = overlay.get_closest_dot(200, 200)
        assert result is None

    def test_returns_closest_of_multiple(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        dots.add("Press", 200, 200)
        result = overlay.get_closest_dot(195, 195)
        assert result.x == 200


class TestOverlayRefresh:
    def test_refresh_calls_update_detail(self, overlay_setup):
        overlay, _, detail_calls = overlay_setup
        overlay.refresh()
        assert len(detail_calls) == 1

    def test_refresh_redraws_canvas(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        overlay.refresh()
        items = overlay.canvas.find_all()
        assert len(items) > 0


class TestOverlayAddDot:
    def test_add_dot_on_empty_space(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        event = tk.Event()
        event.x = 100
        event.y = 200
        overlay.add_dot(event)
        assert len(dots) == 1
        assert dots.dots[0].x == 100
        assert dots.dots[0].y == 200

    def test_add_dot_near_existing_does_nothing(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        event = tk.Event()
        event.x = 105
        event.y = 105
        overlay.add_dot(event)
        assert len(dots) == 1


class TestOverlayMoveDot:
    def test_move_current_viewed_dot(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        dots.current_viewed_dot = dots.dots[0]
        event = tk.Event()
        event.x = 200
        event.y = 300
        overlay.move_dot(event)
        assert dots.dots[0].x == 200
        assert dots.dots[0].y == 300

    def test_move_without_current_dot_does_nothing(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        event = tk.Event()
        event.x = 200
        event.y = 300
        overlay.move_dot(event)
        assert dots.dots[0].x == 100


class TestOverlayRemoveOrReassign:
    def test_remove_unbound_dot(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        event = tk.Event()
        event.x = 100
        event.y = 100
        overlay.remove_or_reassign_dot(event)
        assert dots.dots[0] is None

    def test_reassign_bound_dot(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        from pynput.keyboard import KeyCode
        dots.add("Press", 100, 100)
        dots.dots[0].key = KeyCode.from_char("a")
        event = tk.Event()
        event.x = 100
        event.y = 100
        overlay.remove_or_reassign_dot(event)
        assert dots.dots[0] is not None
        assert dots.dots[0].key is None

    def test_remove_clears_current_viewed(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        dots.current_viewed_dot = dots.dots[0]
        event = tk.Event()
        event.x = 100
        event.y = 100
        overlay.remove_or_reassign_dot(event)
        assert dots.current_viewed_dot is None


class TestOverlayDetailDot:
    def test_detail_sets_current_viewed(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        event = tk.Event()
        event.x = 100
        event.y = 100
        overlay.detail_dot(event)
        assert dots.current_viewed_dot == dots.dots[0]

    def test_detail_far_away_does_nothing(self, overlay_setup):
        overlay, dots, _ = overlay_setup
        dots.add("Press", 100, 100)
        event = tk.Event()
        event.x = 500
        event.y = 500
        overlay.detail_dot(event)
        assert dots.current_viewed_dot is None
