"""Test sky projection module."""

from numpy.testing import assert_array_almost_equal as assert_array

from matplotlib.path import Path

from pyvims.projections import Sky
from pyvims.angles import DEC, RA

from pytest import fixture, raises


@fixture
def proj():
    """Sky projection."""
    return Sky()


def test_sky_attr():
    """Test sky projection attributes."""
    proj = Sky(ra=10, dec=25, twist=50)

    assert str(proj) == 'Sky'

    assert isinstance(proj.ra, RA)
    assert isinstance(proj.dec, DEC)

    assert proj.ra == 10
    assert proj.dec == 25
    assert proj.twist == 50

    assert_array(proj.pointing, (10, 25, 50))


def test_sky_matrix():
    """Test sky rotation matrix."""
    assert_array(Sky().m, [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ])

    assert_array(Sky(ra=90).m, [
        [0, 1, 0],
        [-1, 0, 0],
        [0, 0, 1],
    ])

    assert_array(Sky(ra=180).m, [
        [-1, 0, 0],
        [0, -1, 0],
        [0, 0, 1],
    ])

    assert_array(Sky(ra=-90).m, [
        [0, -1, 0],
        [1, 0, 0],
        [0, 0, 1],
    ])

    assert_array(Sky(dec=90).m, [
        [0, 0, 1],
        [0, 1, 0],
        [-1, 0, 0],
    ])

    assert_array(Sky(dec=-90).m, [
        [0, 0, -1],
        [0, 1, 0],
        [1, 0, 0],
    ])

    assert_array(Sky(twist=90).m, [
        [1, 0, 0],
        [0, 0, 1],
        [0, -1, 0],
    ])

    assert_array(Sky(twist=-90).m, [
        [1, 0, 0],
        [0, 0, -1],
        [0, 1, 0],
    ])

    assert_array(Sky(twist=180).m, [
        [1, 0, 0],
        [0, -1, 0],
        [0, 0, -1],
    ])

    assert_array(Sky(ra=90, dec=90).m, [
        [0, 0, 1],
        [-1, 0, 0],
        [0, -1, 0],
    ])

    assert_array(Sky(ra=90, dec=90, twist=90).m, [
        [0, 0, 1],
        [0, -1, 0],
        [1, 0, 0],
    ])


def test_sky_xy(proj):
    """Test Sky projection in map projection."""
    assert_array(proj(0, 0), (0, 0))
    assert_array(proj(10, 0), (.176, 0), decimal=3)
    assert_array(proj(-10, 0), (-.176, 0), decimal=3)
    assert_array(proj(0, 10), (0, .176), decimal=3)
    assert_array(proj(0, -10), (0, -.176), decimal=3)

    assert_array(proj([0, 10, -10], 0), [
        [0, .176, -.176],
        [0, 0, 0],
    ], decimal=3)

    assert_array(proj(0, [0, 10, -10]), [
        [0, 0, 0],
        [0, .176, -.176],
    ], decimal=3)

    assert_array(proj([10, -10, 0, 0], [0, 0, 10, -10]), [
        [.176, -.176, 0, 0],
        [0, 0, .176, -.176],
    ], decimal=3)

    assert_array(proj([[10, -10], [0, 0]], [[0, 0], [10, -10]]), [
        [[.176, -.176], [0, 0]],
        [[0, 0], [.176, -.176]],
    ], decimal=3)

    with raises(ValueError):
        _ = proj([0], [0, 0])  # Invalid array size

    proj = Sky(ra=10)
    assert_array(proj(0, 0), (-.176, 0), decimal=3)
    assert_array(proj(10, 0), (0, 0))
    assert_array(proj(20, 0), (.176, 0), decimal=3)

    proj = Sky(dec=10)
    assert_array(proj(0, 0), (0, -.176), decimal=3)
    assert_array(proj(0, 10), (0, 0))
    assert_array(proj(0, 20), (0, .176), decimal=3)

    proj = Sky(twist=90)
    assert_array(proj(0, 0), (0, 0))
    assert_array(proj(10, 0), (0, -.176), decimal=3)
    assert_array(proj(0, 10), (.176, 0), decimal=3)


def test_sky_radec(proj):
    """Test Sky reverse projection in map projection."""
    assert_array(proj(0, 0, invert=True), (0, 0))
    assert_array(proj(.176, 0, invert=True), (10, 0), decimal=1)
    assert_array(proj(-.176, 0, invert=True), (350, 0), decimal=1)
    assert_array(proj(0, .176, invert=True), (0, 10), decimal=1)
    assert_array(proj(0, -.176, invert=True), (0, -10), decimal=1)

    assert_array(proj([0, .176, -.176], 0, invert=True), [
        [0, 10, 350],
        [0, 0, 0],
    ], decimal=1)

    assert_array(proj(0, [0, .176, -.176], invert=True), [
        [0, 0, 0],
        [0, 10, -10],
    ], decimal=1)

    assert_array(
        proj(
            [0, .176, -.176, 0, 0],
            [0, 0, 0, .176, -.176],
            invert=True,
        ),
        [
            [0, 10, 350, 0, 0],
            [0, 0, 0, 10, -10],
        ], decimal=1)

    assert_array(
        proj(
            [[.176, -.176], [0, 0]],
            [[0, 0], [.176, -.176]],
            invert=True,
        ),
        [
            [[10, 350], [0, 0]],
            [[0, 0], [10, -10]],
        ], decimal=1)

    with raises(ValueError):
        _ = proj([0], [0, 0], invert=True)  # Invalid array size

    proj = Sky(ra=10)
    assert_array(proj(-.176, 0, invert=True), (0, 0), decimal=1)
    assert_array(proj(0, 0, invert=True), (10, 0), decimal=1)
    assert_array(proj(.176, 0, invert=True), (20, 0), decimal=1)

    proj = Sky(dec=10)
    assert_array(proj(0, -.176, invert=True), (0, 0), decimal=1)
    assert_array(proj(0, 0, invert=True), (0, 10), decimal=1)
    assert_array(proj(0, .176, invert=True), (0, 20), decimal=1)

    proj = Sky(twist=90)
    assert_array(proj(0, 0, invert=True), (0, 0), decimal=1)
    assert_array(proj(0, -.176, invert=True), (10, 0), decimal=1)
    assert_array(proj(.176, 0, invert=True), (0, 10), decimal=1)


def test_sky_path(proj):
    """Test sky projection on Path."""
    path = proj(Path([
        (10, 0),
        (0, 10),
        (-10, 0),
        (0, -10),
    ]))

    assert len(path.vertices) == 5

    assert_array(path.vertices, [
        [.176, 0],
        [0, .176],
        [-.176, 0],
        [0, -.176],
        [.176, 0],  # Added
    ], decimal=3)

    assert_array(
        path.codes,
        [Path.MOVETO] + 3 * [Path.LINETO] + [Path.CLOSEPOLY]
    )
