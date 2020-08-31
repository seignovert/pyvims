"""Test image projection module."""

from pathlib import Path

from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.pyplot import imread

from pyvims.projections import Orthographic, Stereographic, bg_pole

from pytest import fixture


DATA = Path(__file__).parent / 'data'


@fixture
def bw_png():
    """Black and white background map in PNG."""
    return imread(DATA / 'Titan_ISS.png')

@fixture
def rgb_jpg():
    """RGB background map in JPG."""
    return imread(DATA / 'Titan_VIMS_ISS.jpg')


@fixture
def npole_ortho():
    """Default North Pole Orthographic projection."""
    return Orthographic(lat_0=90)

@fixture
def spole_stereo():
    """Default North Pole Orthographic projection."""
    return Stereographic(lat_0=-90)


def test_bg_pole_bw_png_ortho_npole(bw_png, npole_ortho):
    """Test polar projection on BW-PNG basemap in North Pole Ortho."""
    img, extent = bg_pole(bw_png, npole_ortho, lat_1=0)

    assert img.shape == (1024, 1024, 4)

    assert_array(img[0, 0], [0.423, 0.423, 0.423, 0], decimal=3)
    assert_array(img[512, 512], [0.568, 0.568, 0.568, 1], decimal=3)

    assert_array(extent, [-1, 1, -1, 1], decimal=3)


def test_bg_pole_rgb_jpg_stereo_spole(rgb_jpg, spole_stereo):
    """Test polar projection on RGB-JPG basemap in South Pole Stereo."""
    img, extent = bg_pole(rgb_jpg, spole_stereo, n=128)

    assert img.shape == (128, 128, 4)
    assert_array(img[0, 0], [189, 167, 144, 0])
    assert_array(img[64, 64], [172, 147, 125, 255])

    assert_array(extent, [-7.464, 7.464, -7.464, 7.464], decimal=3)
