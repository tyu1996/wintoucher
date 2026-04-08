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
