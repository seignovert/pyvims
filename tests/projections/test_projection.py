"""Test stereographic projection module."""

import numpy as np

from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

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

def test_projection_path_patch_collection():
    """Test stereographic projection on Path, Patch and Collection."""
    proj = Projection()

    assert proj.xy_path(None) is None

    _patch = PathPatch(None, facecolor='r', edgecolor='b', alpha=.5)
    _coll = PatchCollection([_patch])

    assert proj(_patch).get_path() is None
    assert proj(_coll).get_paths()[0] is None
