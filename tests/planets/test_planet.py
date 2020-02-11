"""Test planet module."""

from pyvims.planets import Titan


def test_planet_attr():
    """Test planet attributes."""
    assert str(Titan) == 'Titan'
    assert Titan == 'Titan'
    assert Titan == 'TITAN'
    assert Titan == 'titan'

    assert Titan.radius == Titan.r == 2574.73
    assert Titan.MEAN_RADIUS == (2574.73, 0.09)

    assert Titan.radii == (2574.32, 2574.36, 2574.91)
    assert Titan.a == 2574.32
    assert Titan.b == 2574.36
    assert Titan.c == 2574.91
