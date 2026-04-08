from unittest.mock import patch

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
        item.update()
        item.move(150, 250)
        item.update()
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
        with patch("wintoucher.util.touch.windll") as mock_windll:
            mock_windll.user32.InitializeTouchInjection.return_value = 1
            mock_windll.user32.InjectTouchInput.return_value = 1
            from wintoucher.util.touch import TouchManager
            mgr = TouchManager(4)
            mgr.down(0, 100, 200)
            mgr.apply_touches()
            mock_windll.user32.InjectTouchInput.assert_called()

    def test_apply_touches_no_enabled_skips_inject(self):
        mgr, mock_windll = self._make_manager()
        mock_windll.user32.InjectTouchInput.reset_mock()
        mgr.apply_touches()
        mock_windll.user32.InjectTouchInput.assert_not_called()

    def test_apply_touches_inject_failure_raises(self):
        with patch("wintoucher.util.touch.windll") as mock_windll:
            mock_windll.user32.InitializeTouchInjection.return_value = 1
            mock_windll.user32.InjectTouchInput.return_value = 0
            from wintoucher.util.touch import TouchManager
            mgr = TouchManager(4)
            mgr.down(0, 100, 200)
            with pytest.raises(TouchError, match="Failed trying to update"):
                mgr.apply_touches()

    def test_full_down_apply_up_apply_cycle(self):
        with patch("wintoucher.util.touch.windll") as mock_windll:
            mock_windll.user32.InitializeTouchInjection.return_value = 1
            mock_windll.user32.InjectTouchInput.return_value = 1
            from wintoucher.util.touch import TouchManager
            mgr = TouchManager(4)
            mgr.down(0, 100, 200)
            mgr.apply_touches()
            assert mgr.touches[0].enabled is True
            assert mgr.touches[0].touch_info.pointerInfo.pointerFlags == TouchItem.UPDATE_STATE

            mgr.up(0)
            mgr.apply_touches()
            assert mgr.touches[0].enabled is False
