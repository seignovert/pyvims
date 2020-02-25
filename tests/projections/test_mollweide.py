"""Test mollweide projection module."""

import numpy as np
from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

from pyvims.projections import Mollweide

from pytest import fixture, raises


@fixture
def proj():
    """Mollweide projection."""
    return Mollweide()

def test_moll():
    """Test mollweide projection."""
    proj = Mollweide(target='Titan')

    assert str(proj) == 'Mollweide'
    assert proj.PROJ4 == 'moll'

    assert proj.lon_w_0 == 0
    assert proj.r == 2574730
    assert proj.rx == 2574730 * np.sqrt(2) / (np.pi / 2)
    assert proj.ry == 2574730 * np.sqrt(2)

    assert proj.proj4 == (
        '+proj=moll +lon_0=0 +x_0=0 +y_0=0 '
        '+R=2574730.0 +units=m +no_defs')

    assert proj.wkt == (
        'PROJCS["PROJCS_Titan_Mollweide",'
        'GEOGCS["GCS_Titan",'
        'DATUM["D_Titan",'
        'SPHEROID["Titan_Mean_Sphere", 2574730, 0]],'
        'PRIMEM["Greenwich",0],'
        'UNIT["Degree",0.017453292519943295]],'
        'PROJECTION["Mollweide"],'
        'PARAMETER["false_easting", 0],'
        'PARAMETER["false_northing", 0],'
        'PARAMETER["central_meridian", 0],'
        'UNIT["Meter", 1]]')

    assert_array(proj.extent, [
        -2 * 2574730 * np.sqrt(2),
        2 * 2574730 * np.sqrt(2),
        -2574730 * np.sqrt(2),
        2574730 * np.sqrt(2),
    ], decimal=1)


def test_moll_xy(proj):
    """Test mollweide projection values."""
    assert_array(proj(0, 0), (0, 0))
    assert_array(proj(0, 90), (0, 1))
    assert_array(proj(0, 90 - 1e-12), (0, 1), decimal=6)
    assert_array(proj(0, -90), (0, -1))
    assert_array(proj(90, 0), (-1, 0))
    assert_array(proj(180, 0), (-2, 0))
    assert_array(proj(-180, 0), (2, 0))
    assert_array(proj(270, 0), (1, 0))
    assert_array(proj(360, 0), (0, 0))
    assert_array(proj(180, 90), (0, 1))
    assert_array(proj(-180, -90), (0, -1))

    assert_array(
        proj(0, [0, 90, -90]),
        ([0, 0, 0], [0, 1, -1]),
        decimal=1)

    assert_array(
        proj([0, 90, 180, -180, 270, 360], 0),
        ([0, -1, -2, 2, 1, 0], [0, 0, 0, 0, 0, 0]),
        decimal=1)

    assert_array(
        proj(
            [0, 0, 0, 90, 180, -180, 270, 360],
            [0, 90, -90, 0, 0, 0, 0, 0]
        ), (
            [0, 0, 0, -1, -2, 2, 1, 0],
            [0, 1, -1, 0, 0, 0, 0, 0]
        ),
        decimal=1)

    assert_array(
        proj(
            [[0, 0, 0, 90], [180, -180, 270, 360]],
            [[0, 90, -90, 0], [0, 0, 0, 0]]
        ), (
            [[0, 0, 0, -1], [-2, 2, 1, 0]],
            [[0, 1, -1, 0], [0, 0, 0, 0]]
        ),
        decimal=1)


def test_moll_lonlat(proj):
    """Test mollweide projection reverse values."""
    assert_array(proj(0, 0, invert=True), (0, 0))
    assert_array(proj(0, 1, invert=True), (0, 90))
    assert_array(proj(0, -1, invert=True), (0, -90))
    assert_array(proj(-1, 0, invert=True), (90, 0))
    assert_array(proj(-2, 0, invert=True), (180, 0))
    assert_array(proj(2, 0, invert=True), (180, 0))  # Not -180° in invert
    assert_array(proj(1, 0, invert=True), (270, 0))
    assert proj(3, 0, invert=True) == (None, None)  # Outside right
    assert proj(2, 1, invert=True) == (None, None)  # Outside top-right
    assert proj(0, 2, invert=True) == (None, None)  # Outside top

    assert_array(
        proj(0, [0, 1, -1, 2], invert=True),
        ([0, 0, 0, np.nan], [0, 90, -90, np.nan]),
        decimal=1)

    assert_array(
        proj([0, -1, -2, 2, 1, 3], 0, invert=True),
        ([0, 90, 180, 180, 270, np.nan], [0, 0, 0, 0, 0, np.nan]),
        decimal=1)

    assert_array(
        proj(
            [0, 0, 0, 0, -1, -2, 2, 1, 3],
            [0, 1, -1, 2, 0, 0, 0, 0, 0],
            invert=True
        ), (
            [0, 0, 0, np.nan, 90, 180, 180, 270, np.nan],
            [0, 90, -90, np.nan, 0, 0, 0, 0, np.nan]
        ), decimal=1)

    assert_array(
        proj(
            [[0, 0, 0, 0], [-1, -2, 2, 3]],
            [[0, 1, -1, 2], [0, 0, 0, 0]],
            invert=True
        ), (
            [[0, 0, 0, np.nan], [90, 180, 180, np.nan]],
            [[0, 90, -90, np.nan], [0, 0, 0, np.nan]]
        ), decimal=1)


def test_moll_path(proj):
    """Test mollweide projection on Path."""
    with raises(NotImplementedError):
        _ = proj(Path([
            (20, 30),
            (-10, 0),
            (20, -30),
        ]))

def test_moll_patch(proj):
    """Test mollweide projection on Patch."""
    with raises(NotImplementedError):
        _ = proj(PathPatch(Path([
            (20, 30),
            (-10, 0),
            (20, -30),
        ])))


def test_moll_collection(proj):
    """Test mollweide projection on Collection."""
    with raises(NotImplementedError):
        _ = proj(PatchCollection([
            PathPatch(Path([
                (20, 30),
                (-10, 0),
                (20, -30),
            ]))
        ]))
