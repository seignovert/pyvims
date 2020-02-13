"""Test equirectangular projection module."""

from numpy.testing import assert_array_almost_equal as assert_array

from pyvims.projections import Equirectangular

from pytest import approx, fixture


@fixture
def proj():
    """Equirectangular projection on Titan surface."""
    return Equirectangular(target='Titan')


def test_equi(proj):
    """Test equirectangular projection."""
    assert str(proj) == 'Equirectangular'
    assert proj.PROJ4 == 'eqc'

    assert proj.lat_0 == 0
    assert proj.lon_w_0 == 180
    assert proj.lat_ts == 0
    assert proj.rc == 1
    assert proj.xc == approx(8088753, abs=1)
    assert proj.yc == approx(4044376, abs=1)

    assert proj.proj4 == (
        '+proj=eqc +lat_0=0 +lon_0=180 +lat_ts=0 +x_0=0 +y_0=0 '
        '+a=2574730.0 +b=2574730.0 +units=m +no_defs')

    assert proj.wkt == (
        'PROJCS["PROJCS_Titan_Equirectangular",'
        'GEOGCS["GCS_Titan",'
        'DATUM["D_Titan",'
        'SPHEROID["Titan_Mean_Sphere", 2574730, 0]],'
        'PRIMEM["Greenwich",0],'
        'UNIT["Degree",0.017453292519943295]],'
        'PROJECTION["Equirectangular"],'
        'PARAMETER["false_easting", 0],'
        'PARAMETER["false_northing", 0],'
        'PARAMETER["standard_parallel_1", 0],'
        'PARAMETER["central_meridian", 180],'
        'PARAMETER["latitude_of_origin", 0],'
        'UNIT["Meter", 1]]')


def test_equi_xy(proj):
    """Test equirectangular projection values."""
    assert_array(proj(180, 0), (0, 0))
    assert_array(proj(180, 90), (0, 4044376), decimal=0)
    assert_array(proj(180, -90), (0, -4044376), decimal=0)
    assert_array(proj(0, 0), (8088753, 0), decimal=0)
    assert_array(proj(90, 0), (4044376, 0), decimal=0)
    assert_array(proj(270, 0), (-4044376, 0), decimal=0)
    assert_array(proj(360, -90), (-8088753, -4044376), decimal=0)

    assert_array(
        proj([0, 90, 180, 270], 0),
        ([8088753, 4044376, 0, -4044376], [0, 0, 0, 0]),
        decimal=0)

    assert_array(
        proj(180, [0, 90, -90]),
        ([0, 0, 0], [0, 4044376, -4044376]),
        decimal=0)

    assert_array(
        proj([180, 0], [90, 0]),
        ([0, 8088753], [4044376, 0]),
        decimal=0)

    assert_array(
        proj([[180], [0]], [[90], [0]]),
        ([[0], [8088753]], [[4044376], [0]]),
        decimal=0)


def test_equi_lonlat(proj):
    """Test equirectangular projection reverse values."""
    assert_array(proj(0, 0, invert=True), (180, 0), decimal=0)
    assert_array(proj(0, 4044376, invert=True), (180, 90), decimal=0)
    assert_array(proj(0, -4044376, invert=True), (180, -90), decimal=0)
    assert_array(proj(8088753, 0, invert=True), (0, 0), decimal=0)
    assert_array(proj(4044376, 0, invert=True), (90, 0), decimal=0)
    assert_array(proj(-4044376, 0, invert=True), (270, 0), decimal=0)
    assert_array(proj(-8088753, -4044376, invert=True), (0, -90), decimal=0)

    assert_array(
        proj([4044376, -4044376], 0, invert=True),
        ([90, 270], [0, 0]),
        decimal=0)

    assert_array(
        proj(0, [4044376, -4044376], invert=True),
        ([180, 180], [90, -90]),
        decimal=0)

    assert_array(
        proj([0, 8088753], [4044376, 0], invert=True),
        ([180, 0], [90, 0]),
        decimal=0)

    assert_array(
        proj([[0], [8088753]], [[4044376], [0]], invert=True),
        ([[180], [0]], [[90], [0]]),
        decimal=0)

def test_equi_lon_w_0():
    """Test equirectangular projection values centered on 0."""
    proj = Equirectangular(lon_w_0=0, target='Titan')

    assert_array(proj(0, 0), (0, 0))
    assert_array(proj(0, 90), (0, 4044376), decimal=0)
    assert_array(proj(0, -90), (0, -4044376), decimal=0)
    assert_array(proj(90, 0), (-4044376, 0), decimal=0)
    assert_array(proj(180, 0), (-8088753, 0), decimal=0)
    assert_array(proj(270, 0), (4044376, 0), decimal=0)
    assert_array(proj(180, 90), (-8088753, 4044376), decimal=0)
    assert_array(proj(-180, -90), (8088753, -4044376), decimal=0)

    assert_array(proj(0, 0, invert=True), (0, 0), decimal=0)
    assert_array(proj(0, 4044376, invert=True), (0, 90), decimal=0)
    assert_array(proj(0, -4044376, invert=True), (0, -90), decimal=0)
    assert_array(proj(-4044376, 0, invert=True), (90, 0), decimal=0)
    assert_array(proj(-8088753, 0, invert=True), (180, 0), decimal=0)
    assert_array(proj(4044376, 0, invert=True), (270, 0), decimal=0)
    assert_array(proj(-8088753, 4044376, invert=True), (180, 90), decimal=0)
    assert_array(proj(8088753, -4044376, invert=True), (180, -90), decimal=0)
