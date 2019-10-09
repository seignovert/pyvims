"""Test VIMS image module."""

from numpy.testing import assert_array_almost_equal as assert_array

from pytest import approx, fixture, raises

from pyvims import VIMS
from pyvims.errors import VIMSError


@fixture
def img_id():
    """Testing image ID."""
    return '1731456416_1'


@fixture
def cube(img_id):
    """Testing cube."""
    return VIMS(img_id)


@fixture
def pixel(cube):
    """Testing pixel (ground and specular)."""
    return cube[6, 32]


@fixture
def limb_pixel(cube):
    """Testing limb pixel."""
    return cube[1, 1]


def test_pixel_err(cube):
    """Test VIMS pixel errors."""
    # Invalid sample value
    with raises(VIMSError):
        cube[0, 1]

    with raises(VIMSError):
        cube[100, 1]

    with raises(VIMSError):
        cube[1.1, 1]

    # Invalid line value
    with raises(VIMSError):
        cube[1, 0]

    with raises(VIMSError):
        cube[1, 100]

    with raises(VIMSError):
        cube[1, 1.1]


def test_pixel_properties(pixel):
    """Test VIMS pixel propertites (ground and specular)."""
    assert str(pixel) == f'1731456416_1-S6_L32'
    assert pixel.s == 6
    assert pixel.l == 32

    assert pixel.i == 6 - 1
    assert pixel.j == 32 - 1

    assert pixel[352] == pixel@5.13 == pixel['5.13'] == pixel@'352'
    assert pixel[339:351] == pixel@'4.91:5.11' == approx(0.162, abs=1e-3)

    assert pixel.et == approx(406035298.3, abs=.1)
    assert_array(pixel.j2000, [0.7299, 0.3066, -0.6109], decimal=4)
    assert pixel.ra == approx(22.79, abs=1e-2)
    assert pixel.dec == approx(-37.66, abs=1e-2)

    assert pixel.lon == -pixel.lon_e == approx(136.97, abs=1e-2)
    assert pixel.lat == approx(80.37, abs=1e-2)
    assert pixel.alt == approx(0, abs=1e-2)
    assert not pixel.limb
    assert pixel.ground

    assert pixel.slon == '136.97°W'
    assert pixel.slat == '80.37°N'
    assert pixel.salt == '0 km (Ground pixel)'

    assert pixel.inc == approx(67.1, abs=.1)
    assert pixel.eme == approx(64.4, abs=.1)
    assert pixel.phase == approx(131.5, abs=.1)

    assert pixel.dist_sc == approx(211868.6, abs=.1)
    assert pixel.res_s == pixel.res_l == pixel.res == approx(104.9, abs=.1)

    assert pixel.is_specular
    assert pixel.specular_lon == approx(141.2, abs=.1)
    assert pixel.specular_lat == approx(79.25, abs=.1)
    assert pixel.specular_angle == approx(65.77, abs=.1)
    assert pixel.specular_dist == approx(195.2, abs=.1)

    assert len(pixel.spectrum) == len(pixel.wvlns)
    assert pixel.wvlns[0] == approx(0.892, abs=1e-3)
    assert pixel.spectrum[0] == approx(0.156, abs=1e-3)


def test_limb_pixel_properties(limb_pixel):
    """Test VIMS limb pixel propertites (not specular)."""
    assert str(limb_pixel) == f'1731456416_1-S1_L1'
    assert limb_pixel.s == 1
    assert limb_pixel.l == 1

    assert limb_pixel.i == 0
    assert limb_pixel.j == 0

    assert limb_pixel.et == approx(406034072.7, abs=.1)
    assert_array(limb_pixel.j2000, [0.7384, 0.2954, -0.6062], decimal=4)
    assert limb_pixel.ra == approx(21.80, abs=1e-2)
    assert limb_pixel.dec == approx(-37.31, abs=1e-2)

    assert limb_pixel.lon == approx(-108.99, abs=1e-2)
    assert limb_pixel.lat == approx(41.17, abs=1e-2)
    assert limb_pixel.alt == approx(1893.58, abs=1e-2)
    assert limb_pixel.limb
    assert not limb_pixel.ground

    assert limb_pixel.slon == '108.99°E'
    assert limb_pixel.slat == '41.17°N'
    assert limb_pixel.salt == '1894 km (Limb pixel)'

    assert limb_pixel.inc == approx(61.4, abs=.1)
    assert limb_pixel.eme == approx(90.0, abs=.1)
    assert limb_pixel.phase == approx(131.7, abs=.1)

    assert limb_pixel.dist_sc == approx(219698.4, abs=.1)
    assert limb_pixel.res == approx(108.7, abs=.1)

    assert limb_pixel.is_specular is None
    assert limb_pixel.specular_lon is None
    assert limb_pixel.specular_lat is None
    assert limb_pixel.specular_angle is None
    assert limb_pixel.specular_dist is None


def test_pixel_properties_err(pixel):
    """Test VIMS pixel propertites erros."""
    # Band invalid
    with raises(VIMSError):
        pixel[1]

    with raises(VIMSError):
        pixel[353]

    # Wavelength invalid
    with raises(VIMSError):
        pixel@.5

    with raises(VIMSError):
        pixel@6.

    # Invalid index
    with raises(VIMSError):
        pixel@(1, 2, 3)


def test_pixel_plot(pixel):
    """Test pixel plot."""
    pixel.plot(title='testing')
