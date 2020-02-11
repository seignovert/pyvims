"""Test planet module."""

from pyvims.planets import PLANETS

from pytest import raises

def test_planets_list():
    """Test planets list."""
    assert len(PLANETS) == 2

    assert 'Titan' in PLANETS  # Capitalize
    assert 'ENCELADUS' in PLANETS  # Uppercase
    assert 'titan' in PLANETS  # Lowercase
    assert 'SUN' not in PLANETS

    for planet in PLANETS:
        assert planet == 'Titan'
        break

    assert PLANETS['Titan'] == 'Titan'

    with raises(KeyError):
        _ = PLANETS['SUN']
