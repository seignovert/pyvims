"""Test VIMS wavelength module."""

import numpy as np

from numpy.testing import assert_array_almost_equal as assert_array

from pyvims.wvlns import CHANNELS, FWHM, SHIFT, VIMS_IR, VIMS_VIS, WLNS, YEARS

from pytest import approx, raises


def test_vims_csv():
    """Test CSV global variables."""
    assert len(CHANNELS) == len(WLNS) == len(FWHM) == 352

    assert CHANNELS[0] == 1
    assert CHANNELS[-1] == 352

    assert WLNS[0] == .350540
    assert WLNS[-1] == 5.1225

    assert FWHM[0] == .007368
    assert FWHM[-1] == .016

    assert len(YEARS) == len(SHIFT) == 58

    assert YEARS[0] == 1999.6
    assert YEARS[-1] == 2017.8

    assert SHIFT[0] == -25.8
    assert SHIFT[-1] == 9.8


def test_vims_ir():
    """Test VIMS IR wavelengths."""
    # Standard wavelengths
    wvlns = VIMS_IR()
    assert len(wvlns) == 256
    assert wvlns[0] == .884210
    assert wvlns[-1] == 5.122500

    # Full-width at half maximum value
    fwhms = VIMS_IR(fwhm=True)
    assert len(fwhms) == 256
    assert fwhms[0] == .012878
    assert fwhms[-1] == .016

    # Wavenumber (cm-1)
    wvnb = VIMS_IR(sigma=True)
    assert len(wvnb) == 256
    assert wvnb[0] == approx(11309.53, abs=1e-2)
    assert wvnb[-1] == approx(1952.17, abs=1e-2)

    # Single band
    assert VIMS_IR(band=97) == .884210
    assert VIMS_IR(band=97, fwhm=True) == .012878
    assert VIMS_IR(band=97, sigma=True) == approx(11309.53, abs=1e-2)
    assert VIMS_IR(band=97, fwhm=True, sigma=True) == approx(164.72, abs=1e-2)

    # Selected bands array
    assert_array(VIMS_IR(band=[97, 352]), [.884210, 5.122500])
    assert_array(VIMS_IR(band=[97, 352], fwhm=True), [.012878, .016])

    # Time offset
    assert VIMS_IR(band=97, year=2002) == approx(.884210, abs=1e-6)
    assert VIMS_IR(band=97, year=2005) == approx(.884210, abs=1e-6)
    assert VIMS_IR(band=97, year=2001.5) == approx(.885410, abs=1e-6)  # +.0012
    assert VIMS_IR(band=97, year=2011) == approx(.890210, abs=1e-6)    # +.006

    # Time offset on all IR bands
    wvlns_2011 = VIMS_IR(year=2011)
    assert len(wvlns_2011) == 256
    assert wvlns_2011[0] == approx(.890210, abs=1e-6)
    assert wvlns_2011[-1] == approx(5.128500, abs=1e-6)

    # No change in FWHM with time
    assert VIMS_IR(band=97, year=2001.5, fwhm=True) == .012878

    # Outside IR band range
    assert np.isnan(VIMS_IR(band=0))
    assert np.isnan(VIMS_IR(band=96, fwhm=True))
    assert np.isnan(VIMS_IR(band=353, sigma=True))


def test_vims_vis():
    """Test VIMS VIS wavelengths."""
    # Standard wavelengths
    wvlns = VIMS_VIS()
    assert len(wvlns) == 96
    assert wvlns[0] == .350540
    assert wvlns[-1] == 1.045980

    # Full-width at half maximum value
    fwhms = VIMS_VIS(fwhm=True)
    assert len(fwhms) == 96
    assert fwhms[0] == .007368
    assert fwhms[-1] == .012480

    # Wavenumber (cm-1)
    wvnb = VIMS_VIS(sigma=True)
    assert len(wvnb) == 96
    assert wvnb[0] == approx(28527.41, abs=1e-2)
    assert wvnb[-1] == approx(9560.41, abs=1e-2)

    # Single band
    assert VIMS_VIS(band=96) == 1.045980
    assert VIMS_VIS(band=96, fwhm=True) == .012480
    assert VIMS_VIS(band=96, sigma=True) == approx(9560.41, abs=1e-2)
    assert VIMS_VIS(band=96, fwhm=True, sigma=True) == approx(114.07, abs=1e-2)

    # Selected bands array
    assert_array(VIMS_VIS(band=[1, 96]), [.350540, 1.045980])
    assert_array(VIMS_VIS(band=[1, 96], fwhm=True), [.007368, .012480])

    # Time offset
    with raises(ValueError):
        _ = VIMS_VIS(band=97, year=2002)

    with raises(ValueError):
        _ = VIMS_VIS(year=2011)

    # Outside IR band range
    assert np.isnan(VIMS_VIS(band=0))
    assert np.isnan(VIMS_VIS(band=97, fwhm=True))
    assert np.isnan(VIMS_VIS(band=353, sigma=True))
