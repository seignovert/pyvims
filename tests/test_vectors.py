"""Test vector module."""

import numpy as np

from pyvims.vectors import areaquad

from pytest import approx


def test_areaquad():
    """Test spherical quadrangle area."""
    assert areaquad(0, -90, 360, 90) == approx(4 * np.pi, abs=1e-6)
    assert areaquad(0, 15, 30, 45) == approx(4 * np.pi * .0187, abs=1e-3)

    assert areaquad(0, 15, 0, 45) == 0
    assert areaquad(0, 15, 30, 15) == 0
