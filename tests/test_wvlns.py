"""Test VIMS wavelength module."""

from pathlib import Path

import numpy as np

from numpy.testing import assert_array_almost_equal as assert_array

from pyvims import QUB
from pyvims.vars import ROOT_DATA
from pyvims.wvlns import (BAD_IR_PIXELS, CHANNELS, FWHM, SHIFT,
                          VIMS_IR, VIMS_VIS, WLNS, YEARS,
                          bad_ir_pixels, ir_multiplexer, ir_hot_pixels,
                          is_hot_pixel, median_spectrum, moving_median,
                          sample_line_axes)

from pytest import approx, raises


DATA = Path(__file__).parent / 'data'


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


def test_bad_ir_pixels():
    """Test bad IR pixels list."""
    csv = np.loadtxt(ROOT_DATA / 'wvlns_std.csv',
                     delimiter=',', usecols=(0, 1, 2, 3),
                     dtype=str, skiprows=98)

    # Extract bad pixels
    wvlns = np.transpose([
        (int(channel), float(wvln) - .5 * float(fwhm), float(fwhm))
        for channel, wvln, fwhm, comment in csv
        if comment
    ])

    # Group bad pixels
    news = [True] + list((wvlns[0, 1:] - wvlns[0, :-1]) > 1.5)
    bads = []
    for i, new in enumerate(news):
        if new:
            bads.append(list(wvlns[1:, i]))
        else:
            bads[-1][1] += wvlns[2, i]

    assert_array(BAD_IR_PIXELS, bads)

    coll = bad_ir_pixels()
    assert len(coll.get_paths()) == len(bads)


def test_moving_median():
    """Test moving median filter."""
    a = [1, 2, 3, 4, 5]
    assert_array(moving_median(a, width=1), a)

    assert_array(moving_median(a, width=3),
                 [1.5, 2, 3, 4, 4.5])

    assert_array(moving_median(a, width=5),
                 [2, 2.5, 3, 3.5, 4])

    assert_array(moving_median(a, width=2),
                 [1.5, 2.5, 3.5, 4.5, 5])

    assert_array(moving_median(a, width=4),
                 [2, 2.5, 3.5, 4, 4.5])


def test_is_hot_pixel():
    """Test hot pixel detector."""
    # Create random signal
    signal = np.random.default_rng().integers(20, size=100)

    # Add hot pixels
    signal[10::20] = 50
    signal[10::30] = 150

    hot_pix = is_hot_pixel(signal)
    assert len(hot_pix) == 100
    assert 3 <= sum(hot_pix) < 6
    assert all(hot_pix[10::30])

    hot_pix = is_hot_pixel(signal, tol=1.5, frac=90)
    assert len(hot_pix) == 100
    assert 6 <= sum(hot_pix) < 12
    assert all(hot_pix[10::20])


def test_sample_line_axes():
    """Test locatation sample and line axes."""
    # 2D case
    assert sample_line_axes((64, 352)) == (0, )
    assert sample_line_axes((256, 32)) == (1, )

    # 3D case
    assert sample_line_axes((32, 64, 352)) == (0, 1)
    assert sample_line_axes((32, 352, 64)) == (0, 2)
    assert sample_line_axes((352, 32, 64)) == (1, 2)

    # 1D case
    with raises(TypeError):
        _ = sample_line_axes((352))

    # No band axis
    with raises(ValueError):
        _ = sample_line_axes((64, 64))


def test_median_spectrum():
    """Test the median spectrum extraction."""
    # 2D cases
    spectra = [CHANNELS, CHANNELS]

    spectrum = median_spectrum(spectra)  # (2, 352)
    assert spectrum.shape == (352,)
    assert spectrum[0] == 1
    assert spectrum[-1] == 352

    spectrum = median_spectrum(np.transpose(spectra))  # (352, 2)
    assert spectrum.shape == (352,)
    assert spectrum[0] == 1
    assert spectrum[-1] == 352

    # 3D cases
    spectra = [[CHANNELS, CHANNELS]]

    spectrum = median_spectrum(spectra)  # (1, 2, 352)
    assert spectrum.shape == (352,)
    assert spectrum[0] == 1
    assert spectrum[-1] == 352

    spectrum = median_spectrum(np.moveaxis(spectra, 1, 2))  # (1, 352, 2)
    assert spectrum.shape == (352,)
    assert spectrum[0] == 1
    assert spectrum[-1] == 352

    spectrum = median_spectrum(np.moveaxis(spectra, 2, 0))  # (352, 1, 2)
    assert spectrum.shape == (352,)
    assert spectrum[0] == 1
    assert spectrum[-1] == 352


def test_ir_multiplexer():
    """Test spectrum split in each IR multiplexer."""
    # Full spectrum
    spec_1, spec_2 = ir_multiplexer(CHANNELS)

    assert len(spec_1) == 128
    assert len(spec_2) == 128

    assert spec_1[0] == 97
    assert spec_1[-1] == 351

    assert spec_2[0] == 98
    assert spec_2[-1] == 352

    # IR spectrum only
    spec_1, spec_2 = ir_multiplexer(CHANNELS[96:])

    assert len(spec_1) == 128
    assert len(spec_2) == 128

    assert spec_1[0] == 97
    assert spec_1[-1] == 351

    assert spec_2[0] == 98
    assert spec_2[-1] == 352

    # 2D spectra
    spectra = [CHANNELS, CHANNELS]
    spec_1, spec_2 = ir_multiplexer(spectra)

    assert len(spec_1) == 128
    assert len(spec_2) == 128

    assert spec_1[0] == 97
    assert spec_1[-1] == 351

    assert spec_2[0] == 98
    assert spec_2[-1] == 352

    # 3D spectra
    spectra = [[CHANNELS, CHANNELS]]
    spec_1, spec_2 = ir_multiplexer(spectra)

    assert len(spec_1) == 128
    assert len(spec_2) == 128

    assert spec_1[0] == 97
    assert spec_1[-1] == 351

    assert spec_2[0] == 98
    assert spec_2[-1] == 352

    # VIS spectrum only
    with raises(ValueError):
        _ = ir_multiplexer(CHANNELS[:96])

    # Dimension too high
    with raises(ValueError):
        _ = ir_multiplexer([[[CHANNELS]]])


def test_ir_hot_pixels():
    """Test IR hot pixel detector from spectra."""
    qub = QUB('1787314297_1', root=DATA)

    # 1D spectrum
    hot_pixels = ir_hot_pixels(qub['BACKGROUND'][0])
    assert len(hot_pixels) == 10
    assert_array(hot_pixels,
                 [105, 119, 124, 168, 239, 240, 275, 306, 317, 331])

    # 2D spectra
    hot_pixels = ir_hot_pixels(qub['BACKGROUND'])
    assert len(hot_pixels) == 10
    assert_array(hot_pixels,
                 [105, 119, 124, 168, 239, 240, 275, 306, 317, 331])
