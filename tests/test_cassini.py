"""Test Cassini module."""

from pathlib import Path

from pyvims.cassini import img_id

from pytest import raises


def test_cassini_img_id():
    """Test Cassini image ID parser."""
    assert img_id('1487096932_1') == '1487096932_1'
    assert img_id('C1487096932_1_ir.cub') == '1487096932_1'
    assert img_id('v1487096932_1_001.qub') == '1487096932_1_001'
    assert img_id(Path('C1487096932_1_ir.cub')) == '1487096932_1'

    with raises(ValueError):
        _ = img_id('112345_1')
