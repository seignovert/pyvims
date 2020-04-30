"""Test vector module."""

import numpy as np
from numpy.testing import assert_array_almost_equal as assert_array

from pyvims.vectors import angle, azimuth, areaquad, vdot

from pytest import approx, raises


def test_areaquad():
    """Test spherical quadrangle area."""
    assert areaquad(0, -90, 360, 90) == approx(4 * np.pi, abs=1e-6)
    assert areaquad(0, 15, 30, 45) == approx(4 * np.pi * .0187, abs=1e-3)

    assert areaquad(0, 15, 0, 45) == 0
    assert areaquad(0, 15, 30, 15) == 0


def test_vdot():
    """Test dot product between two vectors."""
    assert vdot([1, 0, 0], [1, 0, 0]) == 1
    assert vdot([1, 0, 0], [0, 1, 0]) == 0
    assert vdot([1, 0, 0], [0, 0, 1]) == 0
    assert vdot([1, 0, 0], [-1, 0, 0]) == -1

    v1 = np.transpose([[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]])
    v2 = np.transpose([[1, 0, 0], [0, 1, 0], [0, 0, 1], [-1, 0, 0]])

    assert v1.shape == (3, 4)
    assert v2.shape == (3, 4)

    assert_array(vdot([1, 0, 0], v2), [1, 0, 0, -1])
    assert_array(vdot(v2, [1, 0, 0]), [1, 0, 0, -1])

    assert_array(vdot(v1, v2), [1, 0, 0, -1])

    v1 = np.transpose([[[1, 0, 0], [1, 0, 0]], [[1, 0, 0], [1, 0, 0]]])
    v2 = np.transpose([[[1, 0, 0], [0, 1, 0]], [[-1, 0, 0], [0, 0, 1]]])

    assert v1.shape == (3, 2, 2)
    assert v2.shape == (3, 2, 2)

    assert_array(vdot(v1, v2), [[1, 0], [-1, 0]])

    with raises(ValueError):
        _ = vdot([[1, 0, 0]], v1)


def test_angle():
    """Test dot product."""
    assert angle([1, 0, 0], [1, 0, 0]) == 0
    assert angle([1, 0, 0], [0, 1, 0]) == 90
    assert angle([1, 0, 0], [-1, 0, 0]) == 180

    assert angle([1, 0, 0], [2, 0, 0]) == 0
    assert angle([1, 0, 0], [0, 2, 0]) == 90
    assert angle([1, 0, 0], [-2, 0, 0]) == 180

    v1 = np.transpose([[1, 0, 0], [1, 0, 0], [1, 0, 0], [1, 0, 0]])
    v2 = np.transpose([[1, 0, 0], [0, 1, 0], [0, 0, 1], [-1, 0, 0]])

    assert v1.shape == (3, 4)
    assert v2.shape == (3, 4)

    assert_array(angle([1, 0, 0], v2), [0, 90, 90, 180])
    assert_array(angle(v2, [1, 0, 0]), [0, 90, 90, 180])

    assert_array(angle(v1, v2), [0, 90, 90, 180])

    v1 = np.transpose([[[1, 0, 0], [1, 0, 0]], [[1, 0, 0], [1, 0, 0]]])
    v2 = np.transpose([[[1, 0, 0], [0, 1, 0]], [[-1, 0, 0], [0, 0, 1]]])

    assert v1.shape == (3, 2, 2)
    assert v2.shape == (3, 2, 2)

    assert_array(angle(v1, v2), [[0, 90], [180, 90]])


def test_azimuth():
    """Test azimuth illumination angle."""
    assert azimuth(0, 0, 0) == 0
    assert azimuth(10, 0, 0) == 0
    assert azimuth(90, 90, 135) == approx(135)
    assert azimuth(90, 45, 135) == approx(180)

    _azi = 2 * np.degrees(np.arcsin(1 / np.sqrt(3)))

    assert azimuth(60, 60, 60) == approx(_azi)

    # 1D array
    inc, eme, phase = [0, 10, 90, 90, 60], [0, 0, 90, 45, 60], [0, 0, 135, 135, 60]

    assert_array(
        azimuth(inc, eme, phase),
        [0, 0, 135, 180, _azi]
    )

    # 2D array
    inc, eme, phase = [[10, 90], [90, 60]], [[0, 90], [45, 60]], [[0, 135], [135, 60]]

    assert_array(
        azimuth(inc, eme, phase),
        [[0, 135], [180, _azi]]
    )

    with raises(ValueError):
        _ = azimuth(0, [0], [0])

    with raises(ValueError):
        _ = azimuth([0], 0, [0])

    with raises(ValueError):
        _ = azimuth([0], [0], [[0]])
