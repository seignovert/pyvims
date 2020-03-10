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

def test_noodle_cubes(cubes):
    """Test noodle cubes injection."""
    # Single cube
    noodle = VIMSNoodle(cubes[0])

    assert len(noodle) == len(noodle.cubes) == 1
    assert noodle[0] == '1540484434_1_001'
    assert noodle.cubes[0] == '1540484434_1_001'
    assert noodle['1540484434_1_001'] == '1540484434_1_001'

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
