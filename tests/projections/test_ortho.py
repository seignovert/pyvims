"""Test orthographic projection module."""

import numpy as np
from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path

from pyvims.projections import Orthographic

from pytest import fixture


@fixture
def proj():
    """Orthographic projection on Titan surface."""
    return Orthographic(radius=1e-3)


def test_ortho():
    """Test orthographic projection."""
    proj = Orthographic(target='Titan')

    assert str(proj) == 'Orthographic'
    assert proj.PROJ4 == 'ortho'

    assert proj.lat_0 == 0
    assert proj.lon_w_0 == 0

    assert proj.proj4 == (
        '+proj=ortho +lat_0=0 +lon_0=0 +k=1 +x_0=0 +y_0=0 '
        '+a=2574730.0 +b=2574730.0 +units=m +no_defs')

    assert proj.wkt == (
        'PROJCS["PROJCS_Titan_Orthographic",'
        'GEOGCS["GCS_Titan",'
        'DATUM["D_Titan",'
        'SPHEROID["Titan_Mean_Sphere", 2574730, 0]],'
        'PRIMEM["Greenwich",0],'
        'UNIT["Degree",0.017453292519943295]],'
        'PROJECTION["Orthographic"],'
        'PARAMETER["false_easting", 0],'
        'PARAMETER["false_northing", 0],'
        'PARAMETER["scale_factor", 1],'
        'PARAMETER["central_meridian", 0],'
        'PARAMETER["latitude_of_origin", 0],'
        'UNIT["Meter", 1]]')


def test_ortho_xy(proj):
    """Test orthographic projection values."""
    assert_array(proj(0, 0), (0, 0))
    assert_array(proj(90, 0), (-1, 0), decimal=0)
    assert_array(proj(-90, 0), (1, 0), decimal=0)
    assert_array(proj(271, 0), (1, 0), decimal=0)
    assert_array(proj(0, 90), (0, 1), decimal=0)
    assert_array(proj(0, -90), (0, -1), decimal=0)
    assert proj(180, 0) == (None, None)

    assert_array(
        proj([0, 90, 180, -90], 0),
        ([0, -1, np.nan, 1], [0, 0, np.nan, 0]),
        decimal=0)

    assert_array(
        proj([0, 90], [90, 0]),
        ([0, -1], [1, 0]),
        decimal=0)

    assert_array(
        proj([[0], [90]], [[90], [0]]),
        ([[0], [-1]], [[1], [0]]),
        decimal=0)


def test_ortho_lonlat(proj):
    """Test orthographic projection reverse values."""
    assert_array(proj(0, 0, invert=True), (0, 0))
    assert_array(proj(-1, 0, invert=True), (90, 0), decimal=0)
    assert_array(proj(1, 0, invert=True), (270, 0), decimal=0)
    assert_array(proj(0, 1, invert=True), (0, 90), decimal=0)
    assert_array(proj(0, -1, invert=True), (0, -90), decimal=0)

    assert proj(1, 1, invert=True) == (None, None)

    assert_array(
        proj([-1, 1], 0, invert=True),
        ([90, 270], [0, 0]),
        decimal=0)

    assert_array(
        proj([0, -1, 1], [1, 0, 1], invert=True),
        ([0, 90, np.nan], [90, 0, np.nan]),
        decimal=0)

    assert_array(
        proj([[0], [-1]], [[1], [0]], invert=True),
        ([[0], [90]], [[90], [0]]),
        decimal=0)


def test_ortho_path(proj):
    """Test orthographic projection on Path."""
    path = proj(Path([
        (90, 0),
        (0, 90),
        (-90, 0),
        (0, -90),
    ]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [-1, 0],
        [0, 1],
        [1, 0],
        [0, -1],
        [-1, 0],  # Added
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )
