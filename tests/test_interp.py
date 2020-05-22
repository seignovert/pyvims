"""Test Interpolation module."""

from numpy.testing import assert_array_almost_equal as assert_array

from pytest import raises

from pyvims.interp import lin_interp


def test_lin_interp_1d():
    """Test linear interpolation on 1D array."""
    xp = [1, 2, 3, 5]
    fp = [10, 20, 30, 50]

    assert lin_interp(1, xp, fp) == 10
    assert lin_interp(2, xp, fp) == 20
    assert lin_interp(5, xp, fp) == 50
    assert lin_interp(4, xp, fp) == 40

    assert_array(lin_interp([1, 2, 5, 4], xp, fp), [10, 20, 50, 40])


def test_lin_interp_2d():
    """Test linear interpolation on 2D array."""
    xp = [1, 2, 3, 5]
    fp = [
        [10, 20, 30, 50],
        [100, 200, 300, 500],
        [1000, 2000, 3000, 5000],
    ]

    assert_array(lin_interp(1, xp, fp), [10, 100, 1000])
    assert_array(lin_interp(2, xp, fp), [20, 200, 2000])
    assert_array(lin_interp(5, xp, fp), [50, 500, 5000])
    assert_array(lin_interp(4, xp, fp), [40, 400, 4000])

    assert_array(lin_interp([1, 2, 5, 4, 3], xp, fp), [
        [10, 100, 1000],
        [20, 200, 2000],
        [50, 500, 5000],
        [40, 400, 4000],
        [30, 300, 3000],
    ])


def test_lin_interp_err():
    """Test linear interpolation on array errors."""
    xp = [1, 2, 3, 5]
    fp = [10, 20, 30, 50]

    # Below lower limit
    with raises(ValueError):
        _ = lin_interp(0, xp, fp)

    # Above upper limit
    with raises(ValueError):
        _ = lin_interp(10, xp, fp)
