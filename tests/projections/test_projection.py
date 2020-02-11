"""Test stereographic projection module."""

import numpy as np

from pyvims.projections.__main__ import Projection
from pyvims.planets import Titan

from pytest import approx


def test_projection():
    """Test stereographic projection."""
    proj = Projection(lon_w_0=30, target=Titan)

    assert proj.EPSILON == 1e-10
    assert str(proj) == 'Projection'

    assert proj.lat_0 == 0
    assert proj.lon_w_0 == 30
    assert proj.lon_0 == -30

    assert proj.clat0 == 1
    assert proj.slat0 == 0
    assert proj.clon0 == approx(np.sqrt(3) / 2)
    assert proj.slon0 == approx(.5)

    assert proj.target == 'Titan'
    assert proj.radius == Titan.radius
    assert proj.r == Titan.radius * 1e3
