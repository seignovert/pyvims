"""Test angles module."""

from pyvims.angles import Angle, DEC, RA

from pytest import approx, raises


def test_angle_math():
    """Test Angle math operations."""
    angle = Angle(10.625)

    add_angle = 2 + angle

    assert isinstance(add_angle, Angle)
    assert add_angle == 12.625

    radd_angle = angle + 2

    assert isinstance(radd_angle, Angle)
    assert radd_angle == 12.625

    sub_angle = 2 - angle

    assert isinstance(sub_angle, Angle)
    assert sub_angle == -8.625

    rsub_angle = angle - 2

    assert isinstance(rsub_angle, Angle)
    assert rsub_angle == 8.625


def test_ra_parser():
    """Test RA HMS parser."""
    assert RA.parse('12h34m56s') == approx(188.73, abs=1e-2)
    assert RA.parse('12h34m56.789s') == approx(188.73, abs=1e-2)
    assert RA.parse('12:34:56') == approx(188.73, abs=1e-2)
    assert RA.parse('12:34:56.789') == approx(188.73, abs=1e-2)
    assert RA.parse('12 34 56') == approx(188.73, abs=1e-2)
    assert RA.parse('12 34 56.789') == approx(188.73, abs=1e-2)

    with raises(ValueError):
        _ = RA.parse('12d34m56s')

    with raises(ValueError):
        _ = RA.parse('12h34m')


def test_ra_attr():
    """Test RA attributes."""
    ra = RA(10.625)

    assert float(ra) == 10.625
    assert ra == 10.625
    assert RA('00h42m30.000s') == 10.625
    assert str(ra) == ra.hms == '00h42m30.000s'
    assert RA(370.625) == RA(-349.375) == 10.625

    assert isinstance(2 + ra, RA)

    assert ra.hours == approx(0.71, abs=1e-2)
    assert ra.h == 0
    assert ra.minutes == approx(42.50, abs=1e-2)
    assert ra.m == 42
    assert ra.secondes == approx(30.00, abs=1e-2)
    assert ra.s == 30

    assert ra.radians == ra.rad == approx(0.185, abs=1e-3)
    assert ra.cos == approx(0.983, abs=1e-3)
    assert ra.sin == approx(0.184, abs=1e-3)


def test_dec_parser():
    """Test DEC DMS parser."""
    assert DEC.parse('12d34m56s') == approx(12.58, abs=1e-2)
    assert DEC.parse('12d34m56.789s') == approx(12.58, abs=1e-2)
    assert DEC.parse('+12d34m56s') == approx(12.58, abs=1e-2)
    assert DEC.parse('-12d34m56s') == approx(-12.58, abs=1e-2)
    assert DEC.parse('12:34:56') == approx(12.58, abs=1e-2)
    assert DEC.parse('12:34:56.789') == approx(12.58, abs=1e-2)
    assert DEC.parse('12 34 56') == approx(12.58, abs=1e-2)
    assert DEC.parse('12 34 56.789') == approx(12.58, abs=1e-2)
    assert DEC.parse("12°34'56''") == approx(12.58, abs=1e-2)
    assert DEC.parse("12º34'56\"") == approx(12.58, abs=1e-2)
    assert DEC.parse('12°34′56″') == approx(12.58, abs=1e-2)

    with raises(ValueError):
        DEC.parse('12h34m56s')


def test_dec_attr():
    """Test DEC attributes."""
    dec = DEC(12.58)

    assert float(dec) == 12.58
    assert dec == 12.58
    assert DEC('+12°34′48″') == 12.58
    assert str(dec) == dec.dms == '+12°34′48.000″'

    assert isinstance(2 + dec, DEC)

    assert dec.degrees == approx(12.58, abs=1e-2)
    assert dec.d == 12
    assert dec.minutes == approx(34.80, abs=1e-2)
    assert dec.m == 34
    assert dec.secondes == approx(48.00, abs=1e-2)
    assert dec.s == 48

    assert dec.radians == dec.rad == approx(0.220, abs=1e-3)
    assert dec.cos == approx(0.976, abs=1e-3)
    assert dec.sin == approx(0.218, abs=1e-3)

    with raises(ValueError):
        _ = DEC(90.1)

    with raises(ValueError):
        _ = DEC('-91°00′00″')
