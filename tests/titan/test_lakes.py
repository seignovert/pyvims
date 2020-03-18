"""Test Titan lakes module."""

from pyvims.titan.lakes import lakes


def test_lakes():
    """Test lakes loader."""
    assert 'all' in lakes
