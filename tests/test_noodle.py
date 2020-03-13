"""Test VIMS Noodle module."""

from pathlib import Path

from pyvims.noodle import VIMSNoodle
from pyvims.errors import VIMSError

from pytest import fixture, raises


DATA = Path(__file__).parent / 'data'


@fixture
def cubes():
    """Noodle cubes list."""
    return [
        'C1540484434_1_001',
        'C1540484434_1_002',
        'C1540484434_1_003',
    ]


@fixture
def v_noodle(cubes):
    """Vertical noodle object."""
    return VIMSNoodle(cubes, root=DATA, vstack=True)

@fixture
def h_noodle(cubes):
    """Vertical noodle object."""
    return VIMSNoodle(cubes, root=DATA, vstack=False)


def test_noodle_cubes(cubes):
    """Test noodle cubes injection."""
    # Single cube
    noodle = VIMSNoodle(cubes[0], channel='vis')

    assert len(noodle) == len(noodle.cubes) == 1
    assert noodle[0] == '1540484434_1_001'
    assert noodle.cubes[0] == '1540484434_1_001'
    assert noodle['1540484434_1_001'] == '1540484434_1_001'
    assert noodle.channel == 'VIS'

    with raises(ValueError):
        _ = noodle['1540484434_1_004']  # not in list

    # Cubes array
    noodle = VIMSNoodle(cubes, root=DATA)

    assert len(noodle) == len(noodle.cubes) == 3
    assert noodle[0] == noodle.cubes[0] == '1540484434_1_001'
    assert noodle[1] == noodle.cubes[1] == '1540484434_1_002'
    assert noodle[2] == noodle.cubes[2] == '1540484434_1_003'
    assert noodle['1540484434_1_001'] == '1540484434_1_001'
    assert noodle['1540484434_1_002'] == '1540484434_1_002'
    assert noodle['1540484434_1_003'] == '1540484434_1_003'

    # Cubes exploded tuple
    noodle = VIMSNoodle(*cubes, root=[str(DATA), str(DATA), DATA])

    assert len(noodle) == len(noodle.cubes) == 3
    assert noodle[2] == noodle.cubes[2] == '1540484434_1_003'

    for cube in noodle:
        assert cube == '1540484434_1_001'
        break


def test_noodle_cubes_err():
    """Test cube list errrors."""
    # Empty cube list
    with raises(VIMSError):
        _ = VIMSNoodle()

    with raises(VIMSError):
        _ = VIMSNoodle([])

    # Invalid parameter size
    with raises(VIMSError):
        _ = VIMSNoodle('1540484434_1_001', root=[str(DATA), DATA])

    with raises(VIMSError):
        _ = VIMSNoodle('1540484434_1_001', '1540484434_1_002', root=[DATA])


def test_noodle_attr(v_noodle, h_noodle):
    """Test noodle attributes."""
    assert len(v_noodle) == 3
    assert v_noodle.NS == 21
    assert v_noodle.NL == 3
    assert v_noodle.NP == 63
    assert v_noodle.shape == (256, 3, 21)
    assert v_noodle.vstack

    assert len(h_noodle) == 3
    assert h_noodle.NS == 63
    assert h_noodle.NL == 1
    assert h_noodle.NP == 63
    assert h_noodle.shape == (256, 1, 63)
    assert not h_noodle.vstack


def test_noodle_data(v_noodle, h_noodle):
    """Test noodle data stacking."""
    assert v_noodle.data.shape == (256, 3, 21)
    assert v_noodle.data[0, 0, 0] == v_noodle.cubes[0].data[0, 0, 0]
    assert v_noodle.data[1, 0, 0] == v_noodle.cubes[0].data[1, 0, 0]
    assert v_noodle.data[0, 1, 0] == v_noodle.cubes[1].data[0, 0, 0]
    assert v_noodle.data[0, 0, 1] == v_noodle.cubes[0].data[0, 0, 1]
    assert v_noodle.data[-1, -1, -1] == v_noodle.cubes[-1].data[-1, -1, -1]

    assert h_noodle.data.shape == (256, 1, 63)
    assert h_noodle.data[0, 0, 0] == h_noodle.cubes[0].data[0, 0, 0]
    assert h_noodle.data[1, 0, 0] == h_noodle.cubes[0].data[1, 0, 0]
    assert h_noodle.data[0, 0, 1] == h_noodle.cubes[0].data[0, 0, 1]
    assert h_noodle.data[0, 0, 21] == h_noodle.cubes[1].data[0, 0, 0]
    assert h_noodle.data[-1, -1, -1] == h_noodle.cubes[-1].data[-1, -1, -1]
