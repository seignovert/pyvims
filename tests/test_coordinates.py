"""Test coordinates module."""

from pyvims.coordinates import salt, slat, slon, slon_w


def test_lon():
    """Test longitude string."""
    assert slon(0) == slon(.001) == slon(-.001) == slon(360) == '0°'
    assert slon(180) == slon(180.001) == slon(-180) == '180°'
    assert slon(90) == slon(-270) == '90°W'
    assert slon(-90) == slon(270) == '90°E'

    assert slon(90.01) == '90.01°W'
    assert slon(-90.01) == '90.01°E'


def test_lon_w():
    """Test West longitude string."""
    assert slon_w(0) == slon_w(.001) == slon_w(360) == '0°'
    assert slon_w(180) == slon_w(-180) == '180°W'
    assert slon_w(90) == slon_w(-270) == '90°W'
    assert slon_w(-90) == slon_w(270) == '270°W'

    assert slon_w(90.01) == '90.01°W'
    assert slon_w(-90.01) == '269.99°W'


def test_lat():
    """Test latitude string."""
    assert slat(0) == slat(.001) == 'Eq.'
    assert slat(90) == slat(89.999) == 'N.P.'
    assert slat(-90) == slat(-89.999) == 'S.P.'
    assert slat(45) == '45°N'
    assert slat(-45) == '45°S'

    assert slat(45.01) == '45.01°N'
    assert slat(-45.01) == '45.01°S'


def test_alt():
    """Test altitude string."""
    assert salt(0) == salt(.1) == '0 km'
    assert salt(100) == salt(100.1) == '100 km'
