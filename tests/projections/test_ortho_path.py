"""Test equirectangular projection module."""

import numpy as np
from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path

from pyvims.projections import Orthographic
from pyvims.projections import Path3D

from pytest import fixture


@fixture
def proj():
    """Generic orthographic projection."""
    return Orthographic()

@fixture
def npole():
    """Orthographic projection on the North Pole."""
    return Orthographic(lat_0=90)


@fixture
def spole():
    """Orthographic projection on the South Pole."""
    return Orthographic(lat_0=-90)


def test_ortho_path_closed(proj):
    """Test ortho projection on path is closed."""
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
    ], decimal=1)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )

def test_ortho_path3d(proj):
    """Test orthographic projection on Path3d."""
    path = proj(Path3D([
        (90, 0),
        (0, 90),
        (-90, 0),
        (0, -90),
    ], alt=[0, 1e-3, 2e-3, 3e-3]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [-1, 0],
        [0, 2],
        [3, 0],
        [0, -4],
        [-1, 0],  # Added
    ], decimal=1)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )

def test_ortho_npole_path_0(npole):
    """Test orthographic path on the North Pole with 0 intersection."""
    path = npole(Path([
        (30, 70),
        (60, 40),
        (30, 10),
        (0, 40),
    ]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [-0.171, -0.296],
        [-0.663, -0.383],
        [-0.492, -0.852],
        [0., -0.766],
        [-0.171, -0.296],  # Added
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_npole_path_1(npole):
    """Test orthographic path on the North Pole with 1 intersection."""
    path = npole(Path([
        (30, 70),
        (60, 40),
        (30, -20),
        (0, 40),
    ]))

    assert npole.dtheta == 5
    assert len(path.vertices) == 9

    assert_array(path.vertices, [
        [-0.171, -0.296],
        [-0.663, -0.383],
        [-0.628, -0.777],  # GC intersection 1
        [-0.558, -0.829],  # Limb
        [-0.484, -0.874],  # Limb
        [-0.406, -0.913],  # Limb
        [-0.359, -0.933],  # GC intersection 2
        [0., -0.766],
        [-0.171, -0.296],
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 7 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_npole_path_2(npole):
    """Test orthographic path on the North Pole with 2 intersections."""
    path = npole(Path([
        (30, 70),
        (60, -20),
        (30, -40),
        (0, -20),
    ]))

    assert len(path.vertices) == 14

    assert_array(path.vertices, [
        [-0.171, -0.296],
        [-0.834, -0.550],  # GC intersection 1
        [-0.783, -0.621],  # Limb
        [-0.726, -0.687],  # Limb
        [-0.663, -0.747],  # Limb
        [-0.596, -0.802],  # Limb
        [-0.523, -0.851],  # Limb
        [-0.447, -0.894],  # Limb
        [-0.368, -0.929],  # Limb
        [-0.285, -0.958],  # Limb
        [-0.201, -0.979],  # Limb
        [-0.114, -0.993],  # Limb
        [-0.059, -0.998],  # GC intersection 2
        [-0.171, -0.296],
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 12 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_npole_path_reverse(npole):
    """Test orthographic path on the North Pole with reverse limb direction."""
    path = npole(Path([
        (90, 40),
        (120, 10),
        (90, -20),
        (60, 10),
    ]))

    assert len(path.vertices) == 14

    assert_array(path.vertices, [
        [-0.766, 0.],
        [-0.853, 0.492],
        [-0.938, 0.347],   # GC intersection 1
        [-0.964, 0.264],   # Limb
        [-0.984, 0.179],   # Limb
        [-0.996, 0.093],   # Limb
        [-1., 0.006],      # Limb
        [-0.997, -0.082],  # Limb
        [-0.986, -0.168],  # Limb
        [-0.967, -0.253],  # Limb
        [-0.942, -0.337],  # Limb
        [-0.938, -0.347],  # GC intersection 2
        [-0.853, -0.492],
        [-0.766, 0.],
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 12 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_npole_path_none(npole):
    """Test orthographic path on the North Pole only in southern hemisphere."""
    path = npole(Path([
        (30, -10),
        (60, -30),
        (30, -50),
        (0, -30),
    ]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [np.nan, np.nan],
        [np.nan, np.nan],
        [np.nan, np.nan],
        [np.nan, np.nan],
        [np.nan, np.nan],
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_spole_path_0(spole):
    """Test orthographic path on the South Pole with 0 intersection."""
    path = spole(Path([
        (30, -10),
        (60, -30),
        (30, -50),
        (0, -30),
    ]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [-0.492, 0.852],
        [-0.75, 0.433],
        [-0.321, 0.556],
        [0., 0.866],
        [-0.492, 0.852],
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_spole_path_1(spole):
    """Test orthographic path on the South Pole with 1 intersection."""
    path = spole(Path([
        (30, 20),
        (60, -30),
        (30, -50),
        (0, -30),
    ]))

    assert spole.dtheta == 5
    assert len(path.vertices) == 10

    assert_array(path.vertices, [
        [-0.662, 0.748],  # GC intersection 1
        [-0.75, 0.433],
        [-0.321, 0.556],
        [0., 0.866],
        [-0.316, 0.948],  # GC intersection 2
        [-0.398, 0.917],  # Limb
        [-0.476, 0.879],  # Limb
        [-0.551, 0.834],  # Limb
        [-0.622, 0.782],  # Limb
        [-0.662, 0.748],  # GC intersection 1 duplicate
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 8 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_spole_path_2(spole):
    """Test orthographic path on the South Pole with 2 intersections."""
    path = spole(Path([
        (30, 50),
        (60, 20),
        (30, -50),
        (0, 20),
    ]))

    assert len(path.vertices) == 13

    assert_array(path.vertices, [
        [-0.799, 0.600],  # GC intersection 1
        [-0.321, 0.556],
        [-0.119, 0.992],  # GC intersection 2
        [-0.205, 0.978],  # Limb
        [-0.290, 0.956],  # Limb
        [-0.372, 0.927],  # Limb
        [-0.452, 0.891],  # Limb
        [-0.528, 0.849],  # Limb
        [-0.600, 0.799],  # Limb
        [-0.667, 0.744],  # Limb
        [-0.729, 0.683],  # Limb
        [-0.786, 0.617],  # Limb
        [-0.799, 0.600],  # GC intersection 1 duplicate
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 11 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_spole_path_none(spole):
    """Test orthographic path on the South Pole only in northen hemisphere."""
    path = spole(Path([
        (30, 10),
        (60, 30),
        (30, 50),
        (0, 30),
    ]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [np.nan, np.nan],
        [np.nan, np.nan],
        [np.nan, np.nan],
        [np.nan, np.nan],
        [np.nan, np.nan],
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )


def test_ortho_spole_path_reverse(spole):
    """Test orthographic path on the South Pole with reverse limb direction."""
    path = spole(Path([
        (90, 40),
        (120, 10),
        (90, -20),
        (60, 10),
    ]))

    assert len(path.vertices) == 12

    assert_array(path.vertices, [
        [-0.938, -0.347],  # GC intersection 1
        [-0.94, 0.],
        [-0.938, 0.347],   # GC intersection 2
        [-0.964, 0.264],   # Limb
        [-0.984, 0.179],   # Limb
        [-0.996, 0.093],   # Limb
        [-1., 0.006],      # Limb
        [-0.997, -0.082],  # Limb
        [-0.986, -0.168],  # Limb
        [-0.967, -0.253],  # Limb
        [-0.942, -0.337],  # Limb
        [-0.938, -0.347],  # GC intersection 1 duplicate
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 10 * [Path.LINETO] + [Path.CLOSEPOLY]
    )
