"""Test equirectangular projection module."""

import numpy as np
from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path

from pyvims.projections import Equirectangular

from pytest import fixture, raises


@fixture
def proj():
    """Equirectangular projection on degree unit surface centered at 180°."""
    return Equirectangular(radius=(180e-3 / np.pi))


@fixture
def proj_0():
    """Equirectangular projection on degree unit surface centered at 0°."""
    return Equirectangular(lon_w_0=0, radius=(180e-3 / np.pi))


def test_equi_path_closed(proj):
    """Test equirectangular projection on path is closed."""
    path = proj(Path([
        (170, 0),
        (180, 10),
        (190, 0),
        (180, -10),
    ], [Path.MOVETO] + 3 * [Path.LINETO]))

    assert len(path.vertices) == len(path.codes) == 5
    assert_array(path.vertices[0], path.vertices[-1])

    assert_array(path.vertices, [
        (10, 0),
        (0, 10),
        (-10, 0),
        (0, -10),
        (10, 0),  # Added
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_npole_right(proj):
    """Test equirectangular projection North Pole crossing (right crossing)."""
    path = proj(Path([
        (300, 60),
        (200, 80),
        (100, 60),
        (20, 80),
    ]))

    assert_array(path.vertices, [
        (-120, 60),
        (-20, 80),
        (80, 60),
        (160, 80),
        (180, 75),
        (180, 90),
        (-180, 90),
        (-180, 75),
        (-120, 60),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 7 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_npole_left(proj):
    """Test equirectangular projection North Pole crossing (left crossing)."""
    path = proj(Path([
        (20, 80),
        (100, 60),
        (200, 80),
        (300, 60),
    ]))

    assert_array(path.vertices, [
        (160, 80),
        (80, 60),
        (-20, 80),
        (-120, 60),
        (-180, 75),
        (-180, 90),
        (180, 90),
        (180, 75),
        (160, 80),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 7 * [Path.LINETO] + [Path.CLOSEPOLY]
    )

def test_equi_path_spole_right(proj):
    """Test equirectangular projection South Pole crossing (right crossing)."""
    path = proj(Path([
        (300, -60),
        (200, -80),
        (100, -60),
        (20, -80),
    ]))

    assert_array(path.vertices, [
        (-120, -60),
        (-20, -80),
        (80, -60),
        (160, -80),
        (180, -75),
        (180, -90),
        (-180, -90),
        (-180, -75),
        (-120, -60),
    ], decimal=0)

def test_equi_path_spole_left(proj):
    """Test equirectangular projection South Pole crossing (left crossing)."""
    path = proj(Path([
        (20, -80),
        (100, -60),
        (200, -80),
        (300, -60),
    ]))

    assert_array(path.vertices, [
        (160, -80),
        (80, -60),
        (-20, -80),
        (-120, -60),
        (-180, -75),
        (-180, -90),
        (180, -90),
        (180, -75),
        (160, -80),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 7 * [Path.LINETO] + [Path.CLOSEPOLY]
    )

def test_equi_path_pole_lon_w_0(proj_0):
    """Test equirectangular projection Pole crossing centered at 0°."""
    path = proj_0(Path([
        (300, 60),
        (200, 80),
        (120, 60),
        (20, 80),
    ]))

    assert_array(path.vertices, [
        (60, 60),
        (160, 80),
        (180, 75),
        (180, 90),
        (-180, 90),
        (-180, 75),
        (-120, 60),
        (-20, 80),
        (60, 60),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 7 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_antimeridian_2_1(proj):
    """Test equirectangular projection anti-meridian crossing (2|1)."""
    path = proj(Path([
        (20, 30),
        (-10, 0),
        (20, -30),
    ]))

    assert_array(path.vertices, [
        (-180, 10),
        (-170, 0),
        (-180, -10),
        (-180, 10),
        (160, 30),
        (180, 10),
        (180, -10),
        (160, -30),
        (160, 30),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 2 * [Path.LINETO] + [Path.CLOSEPOLY]
        + [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_antimeridian_1_2(proj):
    """Test equirectangular projection anti-meridian crossing (1|2)."""
    path = proj(Path([
        (10, 0),
        (-20, 30),
        (-20, -30),
    ]))

    assert_array(path.vertices, [
        (-180, 10),
        (-160, 30),
        (-160, -30),
        (-180, -10),
        (-180, 10),
        (170, 0),
        (180, 10),
        (180, -10),
        (170, 0),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
        + [Path.MOVETO] + 2 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_antimeridian_3_1(proj):
    """Test equirectangular projection anti-meridian crossing (3|1)."""
    path = proj(Path([
        (50, 0),
        (20, 30),
        (-10, 0),
        (20, -30),
    ]))

    assert_array(path.vertices, [
        (-180, 10),
        (-170, 0),
        (-180, -10),
        (-180, 10),
        (130, 0),
        (160, 30),
        (180, 10),
        (180, -10),
        (160, -30),
        (130, 0),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 2 * [Path.LINETO] + [Path.CLOSEPOLY]
        + [Path.MOVETO] + 4 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_antimeridian_2_2(proj):
    """Test equirectangular projection anti-meridian crossing (2|2)."""
    path = proj(Path([
        (20, 40),
        (-10, 10),
        (-10, -10),
        (20, -40),
    ]))

    assert_array(path.vertices, [
        (-180, 20),
        (-170, 10),
        (-170, -10),
        (-180, -20),
        (-180, 20),
        (160, 40),
        (180, 20),
        (180, -20),
        (160, -40),
        (160, 40),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
        + [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_antimeridian_1_3(proj):
    """Test equirectangular projection anti-meridian crossing (1|3)."""
    path = proj(Path([
        (10, 0),
        (-20, 30),
        (-50, 0),
        (-20, -30),
    ]))

    assert_array(path.vertices, [
        (-180, 10),
        (-160, 30),
        (-130, 0),
        (-160, -30),
        (-180, -10),
        (-180, 10),
        (170, 0),
        (180, 10),
        (180, -10),
        (170, 0),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 4 * [Path.LINETO] + [Path.CLOSEPOLY]
        + [Path.MOVETO] + 2 * [Path.LINETO] + [Path.CLOSEPOLY]
    )

def test_equi_path_antimeridian_lon_w_0(proj_0):
    """Test equirectangular projection anti-meridian crossing centered at 0°."""
    path = proj_0(Path([
        (170, 0),
        (200, 30),
        (200, -30),
    ]))

    assert_array(path.vertices, [
        (-170, 0),
        (-180, 10),
        (-180, -10),
        (-170, 0),
        (180, 10),
        (160, 30),
        (160, -30),
        (180, -10),
        (180, 10),
    ], decimal=0)

    assert_array(
        path.codes,
        [Path.MOVETO] + 2 * [Path.LINETO] + [Path.CLOSEPOLY]
        + [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_equi_path_cross_err(proj):
    """Test equirectangular projection for too many crossings."""
    with raises(ValueError):
        _ = proj(Path([
            (10, 0),
            (-10, 0),
            (10, 0),
            (-10, 0),
        ]))
