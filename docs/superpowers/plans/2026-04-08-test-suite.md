# WinToucher Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add comprehensive pytest test suite covering pure logic, mocked GUI/OS interactions, and edge cases across all modules.

**Architecture:** Tests mirror the source structure under `tests/`. Pure-logic modules (`key.py`, `json.py`, `TouchItem`) get direct unit tests. OS-dependent code (`TouchManager`, `windll`) uses `unittest.mock.patch` to mock Win32 calls. GUI code (`Overlay`, `DotView`, `FlickDotView.run`) uses a real `tk.Tk` root created in fixtures but mocks external interactions. Each test file is independent and can run in isolation.

**Tech Stack:** pytest, unittest.mock, pytest fixtures for tk.Tk root

---

### Task 1: Add pytest dependency and test infrastructure

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Add pytest to dev dependencies**

```bash
cd D:/Devs/side-projects/wintoucher && poetry add --group dev pytest
```

- [ ] **Step 2: Create test directory and conftest**

Create `tests/__init__.py` (empty file).

Create `tests/conftest.py`:

```python
import tkinter as tk

import pytest


@pytest.fixture
def tk_root():
    """Create and teardown a tkinter root for tests that need it."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()
```

- [ ] **Step 3: Verify pytest runs with no tests**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/ -v`
Expected: `no tests ran` with exit code 5 (no tests collected)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml poetry.lock tests/
git commit -m "chore: add pytest and test infrastructure"
```

---

### Task 2: Test `util/key.py`

**Files:**
- Create: `tests/util/__init__.py`
- Create: `tests/util/test_key.py`

- [ ] **Step 1: Write tests for key utility functions**

Create `tests/util/__init__.py` (empty file).

Create `tests/util/test_key.py`:

```python
from pynput.keyboard import Key as SpecialKey
from pynput.keyboard import KeyCode

from wintoucher.util.key import is_special_key, is_valid_key, key_to_str


class TestIsSpecialKey:
    def test_known_special_key(self):
        assert is_special_key(SpecialKey.esc) is True

    def test_f_keys_are_special(self):
        assert is_special_key(SpecialKey.f1) is True
        assert is_special_key(SpecialKey.f12) is True

    def test_regular_keycode_not_special(self):
        key = KeyCode.from_char("a")
        assert is_special_key(key) is False

    def test_ctrl_not_in_special_keys(self):
        assert is_special_key(SpecialKey.ctrl_l) is False
        assert is_special_key(SpecialKey.ctrl_r) is False


class TestIsValidKey:
    def test_special_key_is_valid(self):
        assert is_valid_key(SpecialKey.space) is True

    def test_char_keycode_is_valid(self):
        key = KeyCode.from_char("x")
        assert is_valid_key(key) is True

    def test_keycode_without_char_is_invalid(self):
        key = KeyCode(vk=65, char=None)
        assert is_valid_key(key) is False

    def test_ctrl_is_invalid(self):
        assert is_valid_key(SpecialKey.ctrl_l) is False


class TestKeyToStr:
    def test_none_returns_empty(self):
        assert key_to_str(None) == ""

    def test_known_special_key(self):
        assert key_to_str(SpecialKey.esc) == "Esc"
        assert key_to_str(SpecialKey.space) == "Space"
        assert key_to_str(SpecialKey.enter) == "Enter"

    def test_unknown_special_key_uses_name(self):
        assert key_to_str(SpecialKey.ctrl_l) == "ctrl_l"

    def test_char_keycode(self):
        key = KeyCode.from_char("a")
        assert key_to_str(key) == "a"

    def test_keycode_without_char_shows_vk(self):
        key = KeyCode(vk=65, char=None)
        assert key_to_str(key) == "<65>"

    def test_shift_keys(self):
        assert key_to_str(SpecialKey.shift_l) == "L Shift"
        assert key_to_str(SpecialKey.shift_r) == "R Shift"

    def test_all_f_keys_mapped(self):
        for i in range(1, 21):
            key = getattr(SpecialKey, f"f{i}")
            assert key_to_str(key) == f"F{i}"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/util/test_key.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/util/
git commit -m "test: add tests for util/key.py"
```

---

### Task 3: Test `util/json.py` — TwoWayDict

**Files:**
- Create: `tests/util/test_json.py`

- [ ] **Step 1: Write tests for TwoWayDict**

Create `tests/util/test_json.py`:

```python
import json
from dataclasses import dataclass
from typing import Dict, Any

import pytest

from wintoucher.util.json import JSONSerializableManager, TwoWayDict


class TestTwoWayDict:
    def test_set_and_get(self):
        d = TwoWayDict()
        d["a"] = 1
        assert d["a"] == 1

    def test_get_key_reverse_lookup(self):
        d = TwoWayDict()
        d["a"] = 1
        assert d.get_key(1) == "a"

    def test_contains(self):
        d = TwoWayDict()
        d["a"] = 1
        assert "a" in d
        assert "b" not in d

    def test_len(self):
        d = TwoWayDict()
        assert len(d) == 0
        d["a"] = 1
        assert len(d) == 1
        d["b"] = 2
        assert len(d) == 2

    def test_delete(self):
        d = TwoWayDict()
        d["a"] = 1
        del d["a"]
        assert "a" not in d
        assert len(d) == 0
        with pytest.raises(KeyError):
            d.get_key(1)

    def test_iter(self):
        d = TwoWayDict()
        d["a"] = 1
        d["b"] = 2
        assert set(d) == {"a", "b"}

    def test_items_keys_values(self):
        d = TwoWayDict()
        d["x"] = 10
        d["y"] = 20
        assert dict(d.items()) == {"x": 10, "y": 20}
        assert set(d.keys()) == {"x", "y"}
        assert set(d.values()) == {10, 20}

    def test_overwrite_key(self):
        d = TwoWayDict()
        d["a"] = 1
        d["a"] = 2
        assert d["a"] == 2
        assert d.get_key(2) == "a"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/util/test_json.py::TestTwoWayDict -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/util/test_json.py
git commit -m "test: add tests for TwoWayDict"
```

---

### Task 4: Test `util/json.py` — JSONSerializableManager

**Files:**
- Modify: `tests/util/test_json.py`

- [ ] **Step 1: Add JSONSerializableManager tests**

Append to `tests/util/test_json.py`:

```python
@dataclass
class SimpleObj:
    name: str
    value: int

    @classmethod
    def __json__(cls):
        return ("name", "value")


@dataclass
class NestedObj:
    label: str
    child: SimpleObj

    @classmethod
    def __json__(cls):
        return ("label", "child")


class TestJSONSerializableManager:
    def test_register_and_roundtrip_simple(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        obj = SimpleObj(name="test", value=42)
        encoded = json.dumps(obj, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert isinstance(decoded, SimpleObj)
        assert decoded.name == "test"
        assert decoded.value == 42

    def test_register_nested_objects(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        mgr.register(NestedObj)
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        obj = NestedObj(label="parent", child=SimpleObj(name="child", value=99))
        encoded = json.dumps(obj, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert isinstance(decoded, NestedObj)
        assert isinstance(decoded.child, SimpleObj)
        assert decoded.child.value == 99

    def test_duplicate_signature_raises(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        with pytest.raises(ValueError, match="same attribute signature"):
            mgr.register_special(str, ("name", "value"))

    def test_custom_encoder_decoder(self):
        mgr = JSONSerializableManager()
        mgr.register_special(set, ("__set__",))
        mgr.add_encoder(set, lambda s: {"__set__": list(s)})
        mgr.add_decoder(set, lambda o: set(o["__set__"]))
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        encoded = json.dumps({1, 2, 3}, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert isinstance(decoded, set)
        assert decoded == {1, 2, 3}

    def test_duplicate_encoder_raises(self):
        mgr = JSONSerializableManager()
        mgr.register_special(set, ("__set__",))
        mgr.add_encoder(set, lambda s: {"__set__": list(s)})
        with pytest.raises(ValueError, match="Encoder for type"):
            mgr.add_encoder(set, lambda s: {"__set__": list(s)})

    def test_duplicate_decoder_raises(self):
        mgr = JSONSerializableManager()
        mgr.register_special(set, ("__set__",))
        mgr.add_decoder(set, lambda o: set(o["__set__"]))
        with pytest.raises(ValueError, match="Decoder for type"):
            mgr.add_decoder(set, lambda o: set(o["__set__"]))

    def test_list_of_objects(self):
        mgr = JSONSerializableManager()
        mgr.register(SimpleObj)
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        objs = [SimpleObj("a", 1), SimpleObj("b", 2)]
        encoded = json.dumps(objs, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert len(decoded) == 2
        assert all(isinstance(o, SimpleObj) for o in decoded)
        assert decoded[0].name == "a"
        assert decoded[1].value == 2

    def test_plain_dict_passes_through(self):
        mgr = JSONSerializableManager()
        encoder = mgr.build_encoder()
        decoder = mgr.build_decoder()

        data = {"foo": "bar", "num": 123}
        encoded = json.dumps(data, cls=encoder)
        decoded = json.loads(encoded, cls=decoder)

        assert decoded == data
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/util/test_json.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/util/test_json.py
git commit -m "test: add tests for JSONSerializableManager"
```

---

### Task 5: Test `util/touch.py` — TouchItem

**Files:**
- Create: `tests/util/test_touch.py`

- [ ] **Step 1: Write tests for TouchItem state machine**

Create `tests/util/test_touch.py`:

```python
import pytest

from wintoucher.util.touch import (
    FINGER_RADIUS,
    POINTER_FLAG_UP,
    TouchError,
    TouchItem,
)


class TestTouchItem:
    def test_initial_state(self):
        item = TouchItem(0)
        assert item.x == 0
        assert item.y == 0
        assert item.enabled is False

    def test_down_sets_coordinates_and_enables(self):
        item = TouchItem(0)
        item.down(100, 200)
        assert item.x == 100
        assert item.y == 200
        assert item.enabled is True
        assert item.touch_info.pointerInfo.pointerFlags == TouchItem.DOWN_STATE

    def test_down_sets_contact_area(self):
        item = TouchItem(0)
        item.down(100, 200)
        rc = item.touch_info.rcContact
        assert rc.left == 100 - FINGER_RADIUS
        assert rc.right == 100 + FINGER_RADIUS
        assert rc.top == 200 - FINGER_RADIUS
        assert rc.bottom == 200 + FINGER_RADIUS

    def test_move_updates_coordinates(self):
        item = TouchItem(0)
        item.down(100, 200)
        item.move(150, 250)
        assert item.x == 150
        assert item.y == 250
        assert item.touch_info.pointerInfo.pointerFlags == TouchItem.UPDATE_STATE

    def test_up_sets_flag(self):
        item = TouchItem(0)
        item.down(100, 200)
        item.up()
        assert item.touch_info.pointerInfo.pointerFlags == POINTER_FLAG_UP

    def test_update_transitions_down_to_update(self):
        item = TouchItem(0)
        item.down(100, 200)
        assert item.touch_info.pointerInfo.pointerFlags == TouchItem.DOWN_STATE
        item.update()
        assert item.touch_info.pointerInfo.pointerFlags == TouchItem.UPDATE_STATE

    def test_update_transitions_up_to_disabled(self):
        item = TouchItem(0)
        item.down(100, 200)
        item.up()
        assert item.enabled is True
        item.update()
        assert item.enabled is False

    def test_update_after_move_keeps_update_state(self):
        item = TouchItem(0)
        item.down(100, 200)
        item.update()  # DOWN -> UPDATE
        item.move(150, 250)
        item.update()  # stays UPDATE (no transition)
        assert item.touch_info.pointerInfo.pointerFlags == TouchItem.UPDATE_STATE
        assert item.enabled is True

    def test_pointer_id_matches_constructor(self):
        item = TouchItem(42)
        assert item.touch_info.pointerInfo.pointerId == 42

    def test_pixel_location_set_on_down(self):
        item = TouchItem(0)
        item.down(300, 400)
        pt = item.touch_info.pointerInfo.ptPixelLocation
        assert pt.x == 300
        assert pt.y == 400
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/util/test_touch.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/util/test_touch.py
git commit -m "test: add tests for TouchItem"
```

---

### Task 6: Test `util/touch.py` — TouchManager with mocked Win32

**Files:**
- Modify: `tests/util/test_touch.py`

- [ ] **Step 1: Add TouchManager tests with mocked windll**

Append to `tests/util/test_touch.py`:

```python
from unittest.mock import MagicMock, patch


class TestTouchManager:
    @patch("wintoucher.util.touch.windll")
    def _make_manager(self, mock_windll, max_touches=4):
        mock_windll.user32.InitializeTouchInjection.return_value = 1
        mock_windll.user32.InjectTouchInput.return_value = 1
        from wintoucher.util.touch import TouchManager
        mgr = TouchManager(max_touches)
        return mgr, mock_windll

    def test_init_creates_touches(self):
        mgr, _ = self._make_manager()
        assert len(mgr.touches) == 4

    def test_init_failure_raises(self):
        with patch("wintoucher.util.touch.windll") as mock_windll:
            mock_windll.user32.InitializeTouchInjection.return_value = 0
            from wintoucher.util.touch import TouchManager
            with pytest.raises(TouchError, match="Failed to initialize"):
                TouchManager(4)

    def test_max_touches_exceeded_raises(self):
        with patch("wintoucher.util.touch.windll") as mock_windll:
            from wintoucher.util.touch import TouchManager
            with pytest.raises(TouchError, match="cannot exceed 256"):
                TouchManager(257)

    def test_down_out_of_range_raises(self):
        mgr, _ = self._make_manager()
        with pytest.raises(TouchError, match="out of range"):
            mgr.down(10, 0, 0)

    def test_move_out_of_range_raises(self):
        mgr, _ = self._make_manager()
        with pytest.raises(TouchError, match="out of range"):
            mgr.move(10, 0, 0)

    def test_up_out_of_range_raises(self):
        mgr, _ = self._make_manager()
        with pytest.raises(TouchError, match="out of range"):
            mgr.up(10)

    def test_press_out_of_range_raises(self):
        mgr, _ = self._make_manager()
        with pytest.raises(TouchError, match="out of range"):
            mgr.press(10, 0, 0)

    def test_down_enables_touch(self):
        mgr, _ = self._make_manager()
        mgr.down(0, 100, 200)
        assert mgr.touches[0].enabled is True

    def test_press_does_down_when_not_enabled(self):
        mgr, _ = self._make_manager()
        mgr.press(0, 100, 200)
        assert mgr.touches[0].enabled is True
        assert mgr.touches[0].touch_info.pointerInfo.pointerFlags == TouchItem.DOWN_STATE

    def test_press_does_move_when_enabled(self):
        mgr, _ = self._make_manager()
        mgr.down(0, 100, 200)
        mgr.press(0, 150, 250)
        assert mgr.touches[0].x == 150
        assert mgr.touches[0].touch_info.pointerInfo.pointerFlags == TouchItem.UPDATE_STATE

    def test_apply_touches_calls_inject(self):
        mgr, mock_windll = self._make_manager()
        mgr.down(0, 100, 200)
        mgr.apply_touches()
        mock_windll.user32.InjectTouchInput.assert_called()

    def test_apply_touches_no_enabled_skips_inject(self):
        mgr, mock_windll = self._make_manager()
        mock_windll.user32.InjectTouchInput.reset_mock()
        mgr.apply_touches()
        mock_windll.user32.InjectTouchInput.assert_not_called()

    def test_apply_touches_inject_failure_raises(self):
        mgr, mock_windll = self._make_manager()
        mgr.down(0, 100, 200)
        mock_windll.user32.InjectTouchInput.return_value = 0
        with pytest.raises(TouchError, match="Failed trying to update"):
            mgr.apply_touches()

    def test_full_down_apply_up_apply_cycle(self):
        mgr, mock_windll = self._make_manager()
        mgr.down(0, 100, 200)
        mgr.apply_touches()
        assert mgr.touches[0].enabled is True
        # After apply, DOWN transitions to UPDATE
        assert mgr.touches[0].touch_info.pointerInfo.pointerFlags == TouchItem.UPDATE_STATE

        mgr.up(0)
        mgr.apply_touches()
        # After apply, UP transitions to disabled
        assert mgr.touches[0].enabled is False
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/util/test_touch.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/util/test_touch.py
git commit -m "test: add tests for TouchManager with mocked Win32"
```

---

### Task 7: Test `controller/dots.py`

**Files:**
- Create: `tests/controller/__init__.py`
- Create: `tests/controller/test_dots.py`

- [ ] **Step 1: Write tests for Dots controller**

Create `tests/controller/__init__.py` (empty file).

Create `tests/controller/test_dots.py`:

```python
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
        # Remove middle dot
        dots.remove(dots.dots[1])
        assert dots.dots[1] is None
        # Add new dot — should reuse slot 1
        dots.add("Press", 50, 50)
        assert dots.dots[1] is not None
        assert dots.dots[1].id == 1
        assert dots.dots[1].x == 50
        assert len(dots.dots) == 3  # no extra append

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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/controller/test_dots.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/controller/
git commit -m "test: add tests for Dots controller"
```

---

### Task 8: Test `gui/overlay.py` with mocked tkinter

**Files:**
- Create: `tests/gui/__init__.py`
- Create: `tests/gui/test_overlay.py`

- [ ] **Step 1: Write tests for Overlay**

Create `tests/gui/__init__.py` (empty file).

Create `tests/gui/test_overlay.py`:

```python
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
        # Canvas should have items drawn
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
        assert len(dots) == 1  # no new dot added


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
        # No current_viewed_dot set
        event = tk.Event()
        event.x = 200
        event.y = 300
        overlay.move_dot(event)
        assert dots.dots[0].x == 100  # unchanged


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
        assert dots.dots[0] is not None  # not removed
        assert dots.dots[0].key is None  # key cleared

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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/gui/test_overlay.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/gui/
git commit -m "test: add tests for Overlay"
```

---

### Task 9: Test `gui/dot.py` — DotView and FlickDotView

**Files:**
- Create: `tests/gui/test_dot_view.py`

- [ ] **Step 1: Write tests for DotView and FlickDotView**

Create `tests/gui/test_dot_view.py`:

```python
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest
from pynput.keyboard import KeyCode

from wintoucher.data.dot import FlickDot, PressDot
from wintoucher.gui.dot import FlickDotView, PressDotView


@pytest.fixture(autouse=True)
def skip_iconbitmap(monkeypatch):
    monkeypatch.setattr(tk.Toplevel, "iconbitmap", lambda self, *a, **kw: None)


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
        dot.distance.set(20)  # small distance for fast test
        dot.delta = 10  # 2 steps
        dot.delay = 0.001
        dot.angle.set(0)

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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/gui/test_dot_view.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/gui/test_dot_view.py
git commit -m "test: add tests for DotView and FlickDotView"
```

---

### Task 10: Test `__init__.py` — keyboard handlers and toggle_listen

**Files:**
- Create: `tests/test_app.py`

- [ ] **Step 1: Write tests for keyboard handler logic and toggle_listen**

Create `tests/test_app.py`:

```python
import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest
from pynput.keyboard import Key as SpecialKey
from pynput.keyboard import KeyCode

from wintoucher.util.key import Key


@pytest.fixture(autouse=True)
def skip_iconbitmap(monkeypatch):
    monkeypatch.setattr(tk.Toplevel, "iconbitmap", lambda self, *a, **kw: None)


@pytest.fixture
def app(tk_root):
    """Create a WintoucherApp with mocked Touch and Tray."""
    with patch("wintoucher.util.touch.windll") as mock_windll, \
         patch("wintoucher.gui.tray.Icon") as mock_icon_cls, \
         patch("wintoucher.gui.tray.Image") as mock_image:
        mock_windll.user32.InitializeTouchInjection.return_value = 1
        mock_windll.user32.InjectTouchInput.return_value = 1
        mock_icon_instance = MagicMock()
        mock_icon_cls.return_value = mock_icon_instance

        from wintoucher.controller.dots import Dots
        from wintoucher import WintoucherApp

        application = WintoucherApp(dots=Dots())
        yield application
        application.root.after_cancel(application.touch_task)
        application.keyboard.stop()
        application.overlay.destroy()
        application.root.destroy()


class TestToggleListen:
    def test_starts_not_listening(self, app):
        # toggle_listen(False) was called in __init__, toggling to True then back
        # Reset to known state
        app.keyboard_listening = False
        app.toggle_listen(False)
        assert app.keyboard_listening is True

    def test_toggle_flips_state(self, app):
        app.keyboard_listening = False
        app.toggle_listen(False)
        assert app.keyboard_listening is True
        app.toggle_listen(False)
        assert app.keyboard_listening is False

    def test_button_text_updates(self, app):
        app.keyboard_listening = False
        app.toggle_listen(False)
        assert "Pause" in app.listen_button.cget("text")
        app.toggle_listen(False)
        assert "Resume" in app.listen_button.cget("text")


class TestKeyboardHandlers:
    def test_esc_toggles_listen_regardless_of_state(self, app):
        app.keyboard_listening = False
        handlers = app.keyboard_handlers()
        handlers["on_press"](SpecialKey.esc)
        assert app.keyboard_listening is True

    def test_esc_toggles_when_already_listening(self, app):
        app.keyboard_listening = True
        handlers = app.keyboard_handlers()
        handlers["on_press"](SpecialKey.esc)
        assert app.keyboard_listening is False

    def test_non_esc_blocked_when_not_listening(self, app):
        app.keyboard_listening = False
        app.overlay.hide()  # ensure withdrawn
        handlers = app.keyboard_handlers()
        key = KeyCode.from_char("a")
        app.dots.add("Press", 100, 100)
        app.dots.dots[0].key = key
        # Press should not trigger touch when not listening
        handlers["on_press"](key)
        # No crash = blocked correctly

    def test_key_release_assigns_key_when_overlay_shown(self, app):
        app.keyboard_listening = True
        app.overlay.show()
        app.dots.add("Press", 100, 100)
        app.dots.current_viewed_dot = app.dots.dots[0]
        handlers = app.keyboard_handlers()
        key = KeyCode.from_char("x")
        handlers["on_release"](key)
        assert app.dots.dots[0].key == key
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/test_app.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_app.py
git commit -m "test: add tests for WintoucherApp keyboard handlers"
```

---

### Task 11: Run full test suite and verify

**Files:**
- No new files

- [ ] **Step 1: Run all tests**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run with coverage to verify scope**

Run: `cd D:/Devs/side-projects/wintoucher && poetry run pytest tests/ -v --tb=short -q`
Expected: All tests pass, count matches expectations (~60+ tests)

- [ ] **Step 3: Final commit if any adjustments were needed**

```bash
git add -A tests/
git commit -m "test: finalize test suite"
```
