import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest
from pynput.keyboard import KeyCode

from wintoucher.data.dot import FlickDot, PressDot
from wintoucher.gui.dot import FlickDotView, PressDotView


def _make_thread_safe_int_var(value=0):
    """Return a simple object mimicking tk.IntVar but safe to call from any thread."""
    var = MagicMock()
    container = [value]
    var.get.side_effect = lambda: container[0]
    var.set.side_effect = lambda v: container.__setitem__(0, v)
    return var


class TestPressDotView:
    def test_color_with_key(self, tk_root):
        dot = PressDot(id=0, x=100, y=100, key=KeyCode.from_char("a"))
        view = PressDotView(dot)
        assert view.color == "green"

    def test_color_without_key(self, tk_root):
        dot = PressDot(id=0, x=100, y=100, key=None)
        view = PressDotView(dot)
        assert view.color == "snow4"

    def test_draw_creates_oval(self, tk_root):
        canvas = tk.Canvas(tk_root)
        dot = PressDot(id=0, x=100, y=100, key=None)
        view = PressDotView(dot)
        view.draw(canvas, outlined=False)
        items = canvas.find_all()
        assert len(items) >= 1

    def test_draw_with_key_creates_text(self, tk_root):
        canvas = tk.Canvas(tk_root)
        dot = PressDot(id=0, x=100, y=100, key=KeyCode.from_char("a"))
        view = PressDotView(dot)
        view.draw(canvas, outlined=True)
        items = canvas.find_all()
        assert len(items) >= 3  # oval + text + rect background

    def test_detail_returns_type_and_key(self, tk_root):
        dot = PressDot(id=0, x=100, y=100, key=KeyCode.from_char("a"))
        view = PressDotView(dot)
        detail = view.detail(lambda: None)
        assert "Type" in detail
        assert "Key" in detail


class TestFlickDotView:
    def test_color_is_orange(self, tk_root):
        dot = FlickDot(id=0, x=100, y=100, key=KeyCode.from_char("a"))
        view = FlickDotView(dot)
        assert view.color == "orange"

    def test_draw_creates_arrow_and_oval(self, tk_root):
        canvas = tk.Canvas(tk_root)
        dot = FlickDot(id=0, x=100, y=100, key=None)
        view = FlickDotView(dot)
        view.draw(canvas, outlined=False)
        items = canvas.find_all()
        assert len(items) >= 2  # line + oval

    def test_detail_includes_angle_and_distance(self, tk_root):
        dot = FlickDot(id=0, x=100, y=100, key=None)
        view = FlickDotView(dot)
        detail = view.detail(lambda: None)
        assert "Angle" in detail
        assert "Distance" in detail

    def test_stop_sets_running_false(self, tk_root):
        dot = FlickDot(id=0, x=100, y=100, key=None)
        view = FlickDotView(dot)
        view.running = True
        view.stop()
        assert view.running is False


class TestFlickDotViewRun:
    @patch("wintoucher.util.touch.windll")
    def test_run_calls_touch_sequence(self, mock_windll, tk_root):
        mock_windll.user32.InitializeTouchInjection.return_value = 1
        mock_windll.user32.InjectTouchInput.return_value = 1
        from wintoucher.util.touch import TouchManager

        mgr = TouchManager(4)
        dot = FlickDot(id=0, x=100, y=100, key=None)
        # Replace IntVars with thread-safe mocks so the daemon thread can call .get()
        dot.angle = _make_thread_safe_int_var(0)
        dot.distance = _make_thread_safe_int_var(20)  # small distance for fast test
        dot.delta = 10  # 2 steps
        dot.delay = 0.001

        view = FlickDotView(dot)
        view.run(mgr)

        # Wait for thread to finish
        import time
        time.sleep(0.5)

        assert view.running is False
        # InjectTouchInput should have been called multiple times
        assert mock_windll.user32.InjectTouchInput.call_count >= 3  # down + moves + up

    @patch("wintoucher.util.touch.windll")
    def test_run_does_not_start_when_already_running(self, mock_windll, tk_root):
        mock_windll.user32.InitializeTouchInjection.return_value = 1
        mock_windll.user32.InjectTouchInput.return_value = 1
        from wintoucher.util.touch import TouchManager

        mgr = TouchManager(4)
        dot = FlickDot(id=0, x=100, y=100, key=None)
        view = FlickDotView(dot)
        view.running = True  # simulate already running
        view.run(mgr)
        # Should not have started — InjectTouchInput not called
        mock_windll.user32.InjectTouchInput.assert_not_called()
