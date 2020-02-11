"""Test stereographic projection module."""

from numpy.testing import assert_array_almost_equal as assert_array

from pyvims.projections import Stereographic
from pyvims.planets import Titan

def test_stere():
    """Test stereographic projection."""
    proj = Stereographic(target=Titan)

    assert proj.PROJ4 == 'stere'
    assert str(proj) == 'Stereographic'

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

def test_stere_xy():
    """Test stereographic projection values."""
    titan_npole = Stereographic(target=Titan)

    assert_array(titan_npole(0, 90), (0, 0))

    assert_array(
        titan_npole([0, 90, 180, -90], 80),
        ([0, -450519, 0, 450519], [-450519, 0, 450519, 0]),
        decimal=0)

    assert_array(
        titan_npole([0, 90], [80, 80]),
        ([0, -450519], [-450519, 0]),
        decimal=0)

    assert_array(
        titan_npole([[0], [90]], [[80], [80]]),
        ([[0], [-450519]], [[-450519], [0]]),
        decimal=0)

def test_stere_lonlat():
    """Test stereographic projection reverse values."""
    titan_npole = Stereographic(target=Titan)

    assert_array(titan_npole(0, 0, invert=True), (0, 90))

    assert_array(
        titan_npole([-450519, 450519], 0, invert=True),
        ([90, 270], [80, 80]),
        decimal=0)

    assert_array(
        titan_npole([0, -450519], [-450519, 0], invert=True),
        ([0, 90], [80, 80]),
        decimal=0)

    assert_array(
        titan_npole([[0], [-450519]], [[-450519], [0]], invert=True),
        ([[0], [90]], [[80], [80]]),
        decimal=0)
