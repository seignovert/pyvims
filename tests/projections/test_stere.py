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
    assert str(proj) == 'Stereographic'
    assert proj.PROJ4 == 'stere'

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
        'SPHEROID["Titan_Mean_Sphere", 2574730, 0]],'
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


def test_stere_path(proj):
    """Test stereographic projection on Path."""
    path = proj(Path([
        (0, 80),
        (90, 80),
        (180, 80),
        (270, 80),
    ]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [0, -450519],
        [-450519, 0],
        [0, 450519],
        [450519, 0],
        [0, -450519],  # Added
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_stere_patch(proj):
    """Test stereographic projection on Patch."""
    patch = proj(PathPatch(
        Path([
            (0, 80),
            (90, 80),
            (180, 80),
            (270, 80),
        ]),
        facecolor='r',
        edgecolor='b',
        alpha=.5
    ))

    assert_array(patch.get_verts(), [
        [0, -450519],
        [-450519, 0],
        [0, 450519],
        [450519, 0],
        [0, -450519],
    ], decimal=0)

    assert patch.get_facecolor() == (1, 0, 0, .5)
    assert patch.get_edgecolor() == (0, 0, 1, .5)


def test_stere_collection(proj):
    """Test stereographic projection on Collection."""
    coll = proj(PatchCollection(
        [PathPatch(Path([
            (0, 80),
            (90, 80),
            (180, 80),
            (270, 80),
        ]))],
        facecolors='r',
        edgecolors='b',
        alpha=.5))

    assert_array(coll.get_paths()[0].vertices, [
        [0, -450519],
        [-450519, 0],
        [0, 450519],
        [450519, 0],
        [0, -450519],
    ], decimal=0)
    assert_array(coll.get_facecolors()[0], (1, 0, 0, .5))
    assert_array(coll.get_edgecolors()[0], (0, 0, 1, .5))
