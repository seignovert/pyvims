"""Test equirectangular projection."""

import numpy as np

from pytest import approx

from pyvims.projections.equirectangular import pixel_area
from pyvims.vectors import areaquad


def test_pixel_area():
    """Test pixel area in equirectangular projection."""
    img = np.ones((180, 360))
    area = pixel_area(img)

    assert area.shape == (180, 360)
    assert area[0, 0] == area[0, 1] == areaquad(0, 89, 1, 90)
    assert area[90, 0] == areaquad(0, 0, 1, 1)

    assert np.sum(area) == approx(4 * np.pi, abs=1e-6)
    assert np.sum(pixel_area(img, r=10)) == approx(4 * np.pi * 100, abs=1e-6)
