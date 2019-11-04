"""Test Cassini module."""

from pyvims.cassini import img_id


def test_cassini_img_id():
    """Test Cassini image ID parser."""
    assert img_id('1487096932_1') == '1487096932_1'
    assert img_id('C1487096932_1_ir.cub') == '1487096932_1'
    assert img_id('v1487096932_1_001.qub') == '1487096932_1_001'
