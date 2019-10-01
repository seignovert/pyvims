"""Test VIMS image module."""

from pyvims.vims import get_img_id


def test_img_id():
    """Test image ID extraction."""
    assert get_img_id('1487096932_1') == '1487096932_1'
    assert get_img_id('1487096932_1_001') == '1487096932_1_001'
    assert get_img_id('C1487096932_1_vis.cub') == '1487096932_1'
