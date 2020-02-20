"""Test Path 3D module."""

from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path
from matplotlib.patches import PathPatch

from pyvims.projections import Path3D

from pytest import raises


def test_path3d_path():
    """Test path 3D path."""
    path = Path3D([
        (1, 2),
        (3, 4),
        (5, 6)
    ], codes=[
        Path.MOVETO,
        Path.LINETO,
        Path.CLOSEPOLY
    ], alt=[7, 8, 9])

    assert len(path) == 3
    assert_array(path.vertices, [(1, 2), (3, 4), (5, 6)])
    assert_array(path.codes, [1, 2, 79])
    assert_array(path.alt, [7, 8, 9])

    with raises(ValueError):
        _ = Path3D([(1, 2), (3, 4)], alt=10)

    with raises(ValueError):
        _ = Path3D([(1, 2), (3, 4)], alt=[10])

    with raises(ValueError):
        _ = Path3D([(1, 2), (3, 4)], alt=[[10]])


def test_path3d_patch():
    """Test path 3D patch."""
    path = PathPatch(Path3D([
        (1, 2),
        (3, 4),
        (5, 6)
    ], codes=[
        Path.MOVETO,
        Path.LINETO,
        Path.CLOSEPOLY
    ], alt=[7, 8, 9])).get_path()

    assert len(path) == 3
    assert_array(path.vertices, [(1, 2), (3, 4), (5, 6)])
    assert_array(path.codes, [1, 2, 79])
    assert_array(path.alt, [7, 8, 9])
