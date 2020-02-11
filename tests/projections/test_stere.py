"""Test stereographic projection module."""

from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

from pyvims.projections import Stereographic
from pyvims.planets import Titan

from pytest import fixture


@fixture
def proj():
    """Stereographic projection on Titan surface."""
    return Stereographic(target=Titan)


def test_stere(proj):
    """Test stereographic projection."""
    assert proj.PROJ4 == 'stere'
    assert str(proj) == 'Stereographic'

    assert proj.target == 'Titan'
    assert proj.radius == Titan.radius
    assert proj.r == Titan.radius * 1e3

    assert proj.lat_0 == 90
    assert proj.lon_w_0 == 0

    assert proj.proj4 == (
        '+proj=stere +lat_0=90 +lon_0=0 +k=1 +x_0=0 +y_0=0 '
        '+a=2574730.0 +b=2574730.0 +units=m +no_defs')

    assert proj.wkt == (
        'PROJCS["PROJCS_Titan_Stereographic",'
        'GEOGCS["GCS_Titan",'
        'DATUM["D_Titan",'
        'SPHEROID["Titan_MEAN_SPHERE", 2574730, 0]],'
        'PRIMEM["Greenwich",0],'
        'UNIT["Degree",0.017453292519943295]],'
        'PROJECTION["Stereographic"],'
        'PARAMETER["false_easting", 0],'
        'PARAMETER["false_northing", 0],'
        'PARAMETER["scale_factor", 1],'
        'PARAMETER["central_meridian", 0],'
        'PARAMETER["latitude_of_origin", 90],'
        'UNIT["Meter", 1]]')


def test_stere_xy(proj):
    """Test stereographic projection values."""
    assert_array(proj(0, 90), (0, 0))

    assert_array(
        proj([0, 90, 180, -90], 80),
        ([0, -450519, 0, 450519], [-450519, 0, 450519, 0]),
        decimal=0)

    assert_array(
        proj([0, 90], [80, 80]),
        ([0, -450519], [-450519, 0]),
        decimal=0)

    assert_array(
        proj([[0], [90]], [[80], [80]]),
        ([[0], [-450519]], [[-450519], [0]]),
        decimal=0)


def test_stere_lonlat(proj):
    """Test stereographic projection reverse values."""
    assert_array(proj(0, 0, invert=True), (0, 90))

    assert_array(
        proj([-450519, 450519], 0, invert=True),
        ([90, 270], [80, 80]),
        decimal=0)

    assert_array(
        proj([0, -450519], [-450519, 0], invert=True),
        ([0, 90], [80, 80]),
        decimal=0)

    assert_array(
        proj([[0], [-450519]], [[-450519], [0]], invert=True),
        ([[0], [90]], [[80], [80]]),
        decimal=0)


def test_stere_path_patch_collection(proj):
    """Test stereographic projection on Path, Patch and Collection."""
    _vertices = [
        (0, 80),
        (90, 80),
        (180, 80),
        (270, 80),
    ]
    _path = Path(_vertices)
    _patch = PathPatch(_path, facecolor='r', edgecolor='b', alpha=.5)
    _coll = PatchCollection([_patch], facecolors='r', edgecolors='b', alpha=.5)

    path = proj(_path)

    assert len(path.vertices) == len(_vertices)

    assert_array(path.vertices, [
        [0, -450519],
        [-450519, 0],
        [0, 450519],
        [450519, 0],
    ], decimal=0)

    patch = proj(_patch)

    assert_array(patch.get_verts(), [
        [0, -450519],
        [-450519, 0],
        [0, 450519],
        [450519, 0],
        [0, -450519],  # auto-close the polygon
    ], decimal=0)

    assert patch.get_facecolor() == (1, 0, 0, .5)
    assert patch.get_edgecolor() == (0, 0, 1, .5)

    coll = proj(_coll)

    assert_array(coll.get_paths()[0].vertices, [
        [0, -450519],
        [-450519, 0],
        [0, 450519],
        [450519, 0],
    ], decimal=0)
    assert_array(coll.get_facecolors()[0], (1, 0, 0, .5))
    assert_array(coll.get_edgecolors()[0], (0, 0, 1, .5))
