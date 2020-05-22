"""Test VIMS calibration data."""

from pathlib import Path

from pytest import approx, fixture, raises

from pyvims import QUB, VIMS
from pyvims.calib import Efficiency, Multiplier, SolarFlux, Wavelengths


DATA = Path(__file__).parents[1] / 'data'


@fixture
def qub():
    """Test QUB."""
    return QUB('1815243432_1', root=DATA)

@fixture
def cube():
    """Test CUBE."""
    return VIMS('C1540484434_1_001', root=DATA)


def test_mult():
    """Test multiplier calibration data."""
    multiplier_2008_00 = Multiplier(2008)

    assert len(multiplier_2008_00) == 256
    assert multiplier_2008_00[0] == approx(1.731593)
    assert multiplier_2008_00[-1] == approx(1.348164)

    multiplier_2008_50 = Multiplier(2008.5)

    assert len(multiplier_2008_50) == 256
    assert multiplier_2008_50[0] == approx(1.718503)
    assert multiplier_2008_50[-1] == approx(1.351879)

    multiplier_2008_25 = Multiplier(2008.25)

    assert len(multiplier_2008_25) == 256
    assert multiplier_2008_25[0] == approx((1.731593 + 1.718503) / 2)
    assert multiplier_2008_25[-1] == approx((1.348164 + 1.351879) / 2)

    multiplier_2005_25 = Multiplier(2005.25, vis=True)

    assert len(multiplier_2005_25) == 96
    assert multiplier_2005_25[0] == approx(0.921061)
    assert multiplier_2005_25[-1] == approx(0.829441)

    with raises(ValueError):
        _ = Multiplier(1995)

    with raises(ValueError):
        _ = Multiplier(2020)


def test_solar():
    """Test solar flux calibration data."""
    solar_2008_25 = SolarFlux(2008.25)

    assert len(solar_2008_25) == 256
    assert solar_2008_25[0] == approx((946.768738 + 945.505371) / 2)
    assert solar_2008_25[-1] == approx((3.238582 + 3.236702) / 2)

    solar_2005_25 = SolarFlux(2005.25, vis=True)

    assert len(solar_2005_25) == 96
    assert solar_2005_25[0] == approx(1003.907654)
    assert solar_2005_25[-1] == approx(667.124268)


def test_efficiency():
    """Test efficiency calibration data."""
    efficiency_2008_25 = Efficiency(2008.25)

    assert len(efficiency_2008_25) == 256
    assert efficiency_2008_25[0] == approx((7.312818e-9 + 7.306239e-9) / 2)
    assert efficiency_2008_25[-1] == approx((8.762820e-10 + 8.761453e-10) / 2)

    efficiency_2005_25 = Efficiency(2005.25, vis=True)

    assert len(efficiency_2005_25) == 96
    assert efficiency_2005_25[0] == approx(1.937227e-7)
    assert efficiency_2005_25[-1] == approx(6.492614e-8)


def test_wvlns(qub, cube):
    """Test wvlns calibration data."""
    wvlns_2008_25 = Wavelengths(2008.25)

    assert len(wvlns_2008_25) == 256
    assert wvlns_2008_25[0] == approx((0.888310 + 0.889110) / 2)
    assert wvlns_2008_25[-1] == approx((5.127524 + 5.128324) / 2)

    wvlns_2005_25 = Wavelengths(2005.25, vis=True)

    assert len(wvlns_2005_25) == 96
    assert wvlns_2005_25[0] == approx(0.350540)
    assert wvlns_2005_25[-1] == approx(1.045980)

    qub_wvlns = Wavelengths(qub)

    assert len(qub_wvlns) == 256
    assert all(qub_wvlns == Wavelengths(2015.5205))

    cube_wvlns = Wavelengths(cube)

    assert len(cube_wvlns) == 256
    assert max(abs(cube_wvlns - cube.wvlns)) < 5e-4
