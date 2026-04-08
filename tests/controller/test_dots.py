import tkinter as tk

import pytest
from pynput.keyboard import KeyCode

from wintoucher.controller.dots import Dots
from wintoucher.data.dot import FlickDot, PressDot


class TestDotsAdd:
    def test_add_press_dot(self, tk_root):
        dots = Dots()
        dots.add("Press", 100, 200)
        assert len(dots) == 1
        dot = dots.dots[0]
        assert isinstance(dot, PressDot)
        assert dot.x == 100
        assert dot.y == 200
        assert dot.id == 0

    def test_add_flick_dot(self, tk_root):
        dots = Dots()
        dots.add("Flick", 50, 75)
        assert len(dots) == 1
        assert isinstance(dots.dots[0], FlickDot)

    def test_add_invalid_type_raises(self, tk_root):
        dots = Dots()
        with pytest.raises(ValueError, match="Invalid dot type"):
            dots.add("InvalidType", 0, 0)

    def test_add_creates_view(self, tk_root):
        dots = Dots()
        dots.add("Press", 100, 200)
        view = dots.get_view_by_dot(dots.dots[0])
        assert view is not None

    def test_add_sequential_ids(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        dots.add("Press", 20, 20)
        assert dots.dots[0].id == 0
        assert dots.dots[1].id == 1
        assert dots.dots[2].id == 2

    def test_add_reuses_none_slot(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        dots.add("Press", 20, 20)
        dots.remove(dots.dots[1])
        assert dots.dots[1] is None
        dots.add("Press", 50, 50)
        assert dots.dots[1] is not None
        assert dots.dots[1].id == 1
        assert dots.dots[1].x == 50
        assert len(dots.dots) == 3

    def test_add_appends_when_no_none_slots(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        assert len(dots.dots) == 2
        dots.add("Press", 20, 20)
        assert len(dots.dots) == 3
        assert dots.dots[2].id == 2


class TestDotsRemove:
    def test_remove_sets_none(self, tk_root):
        dots = Dots()
        dots.add("Press", 100, 200)
        dot = dots.dots[0]
        dots.remove(dot)
        assert dots.dots[0] is None

    def test_remove_sets_view_none(self, tk_root):
        dots = Dots()
        dots.add("Press", 100, 200)
        dot = dots.dots[0]
        dots.remove(dot)
        assert dots.views[0] is None

    def test_remove_resets_last_operated(self, tk_root):
        dots = Dots()
        dots.add("Press", 100, 200)
        dots.remove(dots.dots[0])
        assert dots._last_operated_dot is None


class TestDotsLen:
    def test_empty(self, tk_root):
        dots = Dots()
        assert len(dots) == 0

    def test_counts_non_none(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        assert len(dots) == 2

    def test_skips_none_in_count(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        dots.remove(dots.dots[0])
        assert len(dots) == 1


class TestDotsIter:
    def test_iter_skips_none(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        dots.add("Press", 20, 20)
        dots.remove(dots.dots[1])
        result = list(dots)
        assert len(result) == 2
        assert result[0].x == 0
        assert result[1].x == 20


class TestDotsLastOperatedDot:
    def test_returns_none_when_empty(self, tk_root):
        dots = Dots()
        assert dots.last_operated_dot is None

    def test_returns_last_added(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        assert dots.last_operated_dot == dots.dots[1]

    def test_setter_with_invalid_dot(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        foreign = PressDot(id=99, x=0, y=0, key=None)
        dots.last_operated_dot = foreign
        assert dots._last_operated_dot is None

    def test_falls_back_to_last_non_none(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        dots.add("Press", 20, 20)
        dots.remove(dots.dots[2])
        dots._last_operated_dot = None
        assert dots.last_operated_dot == dots.dots[1]

    def test_all_none_returns_none(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.remove(dots.dots[0])
        dots._last_operated_dot = None
        assert dots.last_operated_dot is None


class TestDotsCurrentViewedDot:
    def test_returns_none_when_not_set(self, tk_root):
        dots = Dots()
        assert dots.current_viewed_dot is None

    def test_returns_set_dot(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.current_viewed_dot = dots.dots[0]
        assert dots.current_viewed_dot == dots.dots[0]

    def test_returns_none_after_removal(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dot = dots.dots[0]
        dots.current_viewed_dot = dot
        dots.remove(dot)
        assert dots.current_viewed_dot is None

    def test_setter_with_foreign_dot(self, tk_root):
        dots = Dots()
        foreign = PressDot(id=99, x=0, y=0, key=None)
        dots.current_viewed_dot = foreign
        assert dots.current_viewed_dot is None


class TestDotsGetDotsByKey:
    def test_returns_matching_dots(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        key = KeyCode.from_char("a")
        dots.dots[0].key = key
        dots.dots[1].key = key
        result = list(dots.get_dots_by_key(key))
        assert len(result) == 2

    def test_returns_empty_when_no_match(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.dots[0].key = KeyCode.from_char("a")
        result = list(dots.get_dots_by_key(KeyCode.from_char("b")))
        assert len(result) == 0

    def test_skips_none_dots(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dots.add("Press", 10, 10)
        key = KeyCode.from_char("a")
        dots.dots[0].key = key
        dots.dots[1].key = key
        dots.remove(dots.dots[0])
        result = list(dots.get_dots_by_key(key))
        assert len(result) == 1


class TestDotsGetViewByDot:
    def test_returns_view(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        view = dots.get_view_by_dot(dots.dots[0])
        assert view is not None
        assert view.dot == dots.dots[0]

    def test_raises_on_removed_dot_view(self, tk_root):
        dots = Dots()
        dots.add("Press", 0, 0)
        dot = dots.dots[0]
        dots.remove(dot)
        with pytest.raises(AssertionError):
            dots.get_view_by_dot(dot)
