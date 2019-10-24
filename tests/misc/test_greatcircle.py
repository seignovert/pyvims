"""Test great circle module."""

from numpy.testing import assert_array_almost_equal as assert_array

from pyvims.misc.greatcircle import (great_circle, great_circle_arc, great_circle_pole,
                                     great_circle_pole_pts)

from pytest import approx, fixture, raises


@fixture
def pt1():
    """First test point."""
    return 20, 30


@fixture
def pt2():
    """Second test point."""
    return 120, 45


def test_great_circle_arc(pt1, pt2):
    """Test great circle arc."""
    lon, lat = great_circle_arc(*pt1, *pt2, 10)

    assert len(lon) == len(lat) == 10

    assert lon[0] == approx(pt1[0], abs=.1)
    assert lat[0] == approx(pt1[1], abs=.1)

    assert lon[-1] == approx(pt2[0], abs=.1)
    assert lat[-1] == approx(pt2[1], abs=.1)

    assert lon[5] == approx(69.6, abs=.1)
    assert lat[5] == approx(50.8, abs=.1)

    with raises(ValueError):
        _ = great_circle_arc(*pt1, *pt1)


def test_great_circle_lat(pt1, pt2):
    """Test latitude on great circle."""
    assert great_circle(pt1[0], *pt1, *pt2) == approx(pt1[1], abs=.1)
    assert great_circle(pt2[0], *pt1, *pt2) == approx(pt2[1], abs=.1)

    assert great_circle(0, *pt1, *pt2) == approx(9.1, abs=.1)
    assert_array(great_circle([90, 180, 270], *pt1, *pt2),
                 [51.3, -9.1, -51.3], decimal=1)

    with raises(ValueError):
        _ = great_circle(0, *pt1, *pt1)


def test_great_circle_pole_pts(pt1):
    """Test orthogonal points on the great circle from its polar axis."""
    lon1, lat1, lon2, lat2 = great_circle_pole_pts(*pt1)

    assert lon1 == 20
    assert lat1 == -60
    assert lon2 == 110
    assert lat2 == 0


def test_great_circle_pole_lat(pt1):
    """Test orthogonal points on the great circle from its polar axis."""
    assert great_circle_pole(0, *pt1) == approx(-58.4, abs=.1)
    assert_array(great_circle_pole([90, 180, 270], *pt1),
                 [-30.6, 58.4, 30.6], decimal=1)
