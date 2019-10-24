"""Test great circle module."""

from numpy.testing import assert_array_almost_equal as assert_array

from pyvims.misc.greatcircle import (great_circle, great_circle_arc, great_circle_lat,
                                     great_circle_patch, great_circle_path,
                                     great_circle_pole, great_circle_pole_lat,
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


@fixture
def pt3():
    """First test point with negative latitude."""
    return 20, -30


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
    assert great_circle_lat(pt1[0], *pt1, *pt2) == approx(pt1[1], abs=.1)
    assert great_circle_lat(pt2[0], *pt1, *pt2) == approx(pt2[1], abs=.1)

    assert great_circle_lat(0, *pt1, *pt2) == approx(9.1, abs=.1)
    assert_array(great_circle_lat([90, 180, 270], *pt1, *pt2),
                 [51.3, -9.1, -51.3], decimal=1)

    with raises(ValueError):
        _ = great_circle_lat(0, *pt1, *pt1)


def test_great_circle(pt1, pt2):
    """Test great circle coordinates through 2 points."""
    lons, lats = great_circle(*pt1, *pt2, npt=10)

    assert len(lons) == len(lats) == 10

    assert lons[0] == approx(0, abs=.1)
    assert lats[0] == approx(9.1, abs=.1)

    assert lons[-1] == approx(360, abs=.1)
    assert lats[-1] == approx(9.1, abs=.1)

    assert lons[5] == approx(200, abs=.1)
    assert lats[5] == approx(-30, abs=.1)

    lons, lats = great_circle(*pt1, *pt2, npt=10, lon_e=True)

    assert len(lons) == len(lats) == 10

    assert lons[0] == approx(-180, abs=.1)
    assert lats[0] == approx(-9.1, abs=.1)

    assert lons[-1] == approx(180, abs=.1)
    assert lats[-1] == approx(-9.1, abs=.1)

    assert lons[6] == approx(60, abs=.1)
    assert lats[6] == approx(-45, abs=.1)


def test_great_circle_pole_pts(pt1):
    """Test orthogonal points on the great circle from its polar axis."""
    lon1, lat1, lon2, lat2 = great_circle_pole_pts(*pt1)

    assert lon1 == 20
    assert lat1 == -60
    assert lon2 == 110
    assert lat2 == 0


def test_great_circle_pole_lat(pt1):
    """Test orthogonal points on the great circle from its polar axis."""
    assert great_circle_pole_lat(0, *pt1) == approx(-58.4, abs=.1)
    assert_array(great_circle_pole_lat([90, 180, 270], *pt1),
                 [-30.6, 58.4, 30.6], decimal=1)


def test_great_circle_pole(pt1):
    """Test great circle from its polar axis."""
    lons, lats = great_circle_pole(*pt1, npt=10)

    assert len(lons) == len(lats) == 10

    assert lons[0] == approx(0, abs=.1)
    assert lats[0] == approx(-58.4, abs=.1)

    assert lons[-1] == approx(360, abs=.1)
    assert lats[-1] == approx(-58.4, abs=.1)

    assert lons[5] == approx(200, abs=.1)
    assert lats[5] == approx(60, abs=.1)

    lons, lats = great_circle_pole(*pt1, npt=10, lon_e=True)

    assert len(lons) == len(lats) == 10

    assert lons[0] == approx(-180, abs=.1)
    assert lats[0] == approx(58.4, abs=.1)

    assert lons[-1] == approx(180, abs=.1)
    assert lats[-1] == approx(58.4, abs=.1)

    assert lons[4] == approx(-20, abs=.1)
    assert lats[4] == approx(-60, abs=.1)


def test_great_circle_path(pt1, pt3):
    """Test great circle path from its polar axis."""
    path = great_circle_path(*pt1, npt=3, inside=True)

    assert path.vertices.shape == (6, 2)
    assert len(path.codes) == 6

    assert_array(path.vertices[0], [0, -58.4], decimal=1)
    assert_array(path.vertices[:, 0], [0, 180, 360, 360, 0, 0], decimal=1)
    assert_array(path.vertices[:, 1], [-58.4, 58.4, -58.4, 90., 90., -58.4], decimal=1)
    assert_array(path.codes, [1, 2, 2, 2, 2, 79])

    # Internal path with `lat_p >= 0`
    assert path.vertices[-2, 1] == 90

    # External path with `lat_p >= 0`
    assert great_circle_path(*pt1, npt=3, inside=False).vertices[-2, 1] == -90

    # Internal path with `lat_p <= 0`
    assert great_circle_path(*pt3, npt=3, inside=True).vertices[-2, 1] == -90

    # External path with `lat_p <= 0`
    assert great_circle_path(*pt3, npt=3, inside=False).vertices[-2, 1] == 90


def test_great_circle_patch(pt1):
    """Test great circle patch from its polar axis."""
    patch = great_circle_patch(*pt1, npt=3, lon_e=True, inside=False,
                               color='orange', alpha=.1)
    path = patch.get_path()

    assert path.vertices.shape == (6, 2)
    assert path.vertices[0, 0] == -180
    assert path.vertices[-3, 0] == 180
    assert path.vertices[-3, 1] == -90  # not inside + lat_p >= 0

    # Check color and transparency
    assert_array(patch.get_edgecolor(), [1.0, 0.6, 0.0, 0.1], decimal=1)
