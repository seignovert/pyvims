"""Test equirectangular projection module."""

from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path

from pyvims.projections import EquirectangularGC

from pytest import approx, fixture


@fixture
def proj():
    """Equirectangular projection with great circles."""
    return EquirectangularGC(npt_gc=3)


def test_equi():
    """Test equirectangular projection."""
    proj = EquirectangularGC(radius=1)

    assert str(proj) == 'Equirectangular'
    assert proj.PROJ4 == 'eqc'

    assert proj.lat_0 == 0
    assert proj.lon_w_0 == 180
    assert proj.lat_ts == 0
    assert proj.rc == 1
    assert proj.xc == approx(3141, abs=1)  # 1000 * π
    assert proj.yc == approx(1570, abs=1)  # 1000 * π / 2

    assert proj.proj4 == (
        '+proj=eqc +lat_0=0 +lon_0=180 +lat_ts=0 +x_0=0 +y_0=0 '
        '+a=1000.0 +b=1000.0 +units=m +no_defs')

    assert proj.wkt == (
        'PROJCS["PROJCS_Undefined_Equirectangular",'
        'GEOGCS["GCS_Undefined",'
        'DATUM["D_Undefined",'
        'SPHEROID["Undefined_Mean_Sphere", 1000, 0]],'
        'PRIMEM["Greenwich",0],'
        'UNIT["Degree",0.017453292519943295]],'
        'PROJECTION["Equirectangular"],'
        'PARAMETER["false_easting", 0],'
        'PARAMETER["false_northing", 0],'
        'PARAMETER["standard_parallel_1", 0],'
        'PARAMETER["central_meridian", 180],'
        'PARAMETER["latitude_of_origin", 0],'
        'UNIT["Meter", 1]]')


def test_equi_path_gc(proj):
    """Test equirectangular projection with great circles."""
    path = proj(Path([
        (20, 30),
        (-10, 0),
        (20, -30),
    ]))

    assert len(path.vertices) == len(path.codes) == 12

    assert_array(path.vertices, [
        (-180, 11.1),
        (-170, 0),
        (-180, -11.1),
        (-180, 11.1),
        (160, 30),
        (176.1, 15.5),
        (180, 11.1),
        (180, -11.1),
        (176.1, -15.5),
        (160, -30),
        (160, 0),
        (160, 30),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 2 * [Path.LINETO] + [Path.CLOSEPOLY]
        + [Path.MOVETO] + 6 * [Path.LINETO] + [Path.CLOSEPOLY]
    )
