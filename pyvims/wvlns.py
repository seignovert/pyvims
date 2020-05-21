"""VIMS wavelength module."""

import numpy as np

from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection

from .vars import ROOT_DATA


CHANNELS, WLNS, FWHM = np.loadtxt(ROOT_DATA / 'wvlns_std.csv',
                                  delimiter=',', usecols=(0, 1, 2),
                                  unpack=True, skiprows=1)

YEARS, SHIFT = np.loadtxt(ROOT_DATA / 'wvlns_ir_shift.csv',
                          delimiter=',', usecols=(0, 1),
                          unpack=True, skiprows=1)


def VIMS_IR(band=None, year=None, fwhm=False, sigma=False):
    """VIMS IR wavelengths (in microns).

    Corrected for the time shift.

    Parameters
    ----------
    band: int or array, optional
        Get a single band value (get all the bands overwise).
    year: float, optional
        Apply wavelength shift if supply
        (use the standard wavelengths overwise)
    fwhm: bool, optional
        If ``TRUE`` returns the full-width at half maximum value
        instead of the wavelength.
    sigma: bool, optional
        If ``TRUE`` returns wavenumber (cm-1) instead of the wavelength.

    Returns
    -------
    float or array
        Band(s) wavelength(s) (by default) in microns with time offset
        if the year is provided. Based on the optional argument, the
        output could also be the full-width at half maximum value(s)
        or/and the wavenumber(s).

    Note
    ----
    The full-width at half maximum is considered invariant with time.

    See also
    --------
    * https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/
        Cassini/logs/clark-et-al_vims-radiometric-calibration-pds-2018-v2.0-a.pdf
    * https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Cassini/
        logs/VIMS%20IR%20Pixel%20Timing_final-a.pdf

    """
    if band is None:
        band = CHANNELS[96:]

    if not fwhm:
        out = np.interp(band, CHANNELS[96:], WLNS[96:], left=np.nan, right=np.nan)

        if year is not None:
            out += 1e-3 * np.interp(year, YEARS, SHIFT, left=np.nan, right=np.nan)

        if sigma:
            out = 1e4 / out

    else:
        out = np.interp(band, CHANNELS[96:], FWHM[96:], left=np.nan, right=np.nan)

        if sigma:
            wvlns = VIMS_IR(band=band, year=year, fwhm=False, sigma=False)
            out = 1e4 / (wvlns - out / 2) - 1e4 / (wvlns + out / 2)

    return out


def VIMS_VIS(band=None, year=None, fwhm=False, sigma=False):
    """VIMS VIS wavelengths (in microns).

    Parameters
    ----------
    band: int or array, optional
        Get a single band value (get all the bands overwise).
    year: float, optional
        Dummy argument (to match ``VIMS_IR`` arguments).
    fwhm: bool, optional
        If ``TRUE`` returns the full-width at half maximum value
        instead of the wavelength.
    sigma: bool, optional
        If ``TRUE`` returns wavenumber (cm-1) instead of the wavelength.

    Returns
    -------
    float or array
        Band(s) wavelength(s) (by default) in microns with time offset
        if the year is provided. Based on the optional argument, the
        output could also be the full-width at half maximum value(s)
        or/and the wavenumber(s).

    Raises
    ------
    ValueError
        If a ``year`` is provided (no known wavelength shift for the visible).

    Note
    ----
    Not wavelength shift for the visible.

    See also
    --------
    * https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/
        Cassini/logs/clark-et-al_vims-radiometric-calibration-pds-2018-v2.0-a.pdf
    * https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Cassini/
        logs/VIMS%20IR%20Pixel%20Timing_final-a.pdf

    """
    if year is not None:
        raise ValueError('Not wavelength shift known for the visible.')

    if band is None:
        band = CHANNELS[:96]

    if not fwhm:
        out = np.interp(band, CHANNELS[:96], WLNS[:96], left=np.nan, right=np.nan)

        if sigma:
            out = 1e4 / out

    else:
        out = np.interp(band, CHANNELS[:96], FWHM[:96], left=np.nan, right=np.nan)

        if sigma:
            wvlns = VIMS_VIS(band=band, fwhm=False, sigma=False)
            out = 1e4 / (wvlns - out / 2) - 1e4 / (wvlns + out / 2)

    return out


# VIMS-IR order-sorting and poor noisy channels
BAD_IR_PIXELS = [
    (1.5980515, 0.050319),  # Bands: 141-143 (order-sorting filter change)
    (2.9554120, 0.044147),  # Bands: 223-225 (order-sorting filter change)
    (3.8540530, 0.039533),  # Bands: 277-278 (order-sorting filter change)
    (4.7623325, 0.015955),  # Bands: 331 (hot pixel)
    (4.9279810, 0.017740),  # Bands: 341 (slightly noiser, 1.5x at low signal)
    (5.0806185, 0.020883),  # Bands: 350 (slightly noiser, 2x at low signal)
]


def bad_ir_pixels(ymin=-1, ymax=1, color='grey', alpha=.25, **kwargs):
    """VIMS-IR order-sorting and poor signal/noise channels collection."""
    return PatchCollection([
        Rectangle((w_left, ymin), width, ymax - ymin)
        for (w_left, width) in BAD_IR_PIXELS
    ], color=color, alpha=alpha, **kwargs)


def moving_median(arr, width=3):
    """1D moving median filter.

    Parameters
    ----------
    arr: list or numpy.ndarray
        Input list to filter.

    width: int, optional
        Moving box width.

    Returns
    -------
    numpy.ndarray
        Median values.

    Note
    ----
    If the width is an even number, the moving median is done
    on the right value preferentially.

    """
    if width == 1:
        return arr

    n, w = len(arr), width // 2

    _arr = np.full((n + width, width), np.nan)

    for i in range(width):
        _arr[i:i + n, i] = arr

    return np.nanmedian(_arr[w:w + n], axis=1)


def is_hot_pixel(arr, frac=95, tol=2.5):
    """Hot pixel detector.

    This function compute the difference of the pixels
    values with their direct neighboors.
    A pixel is considered a "hot pixel" if this difference
    is larger than ``TOL`` times the difference of ``FRAC %``
    of pixel differences.

    with ``FRAC %`` the fraction of expected valid pixels (apriori)
    and ``TOL`` a thresold criteria.

    Parameters
    ----------
    arr: list or numpy.ndarray
        Input spectra.
    frac: float, optional
        Apriori fraction of valid pixels (95 % by default)
    tol: flat, optional
        Detection thresold criteria (2.5 by default)

    Returns
    -------
    numpy.ndarray
        Boolean array if the pixel is a hot pixel.

    See Also
    --------
    :py:func:`moving_median`

    """
    diff = np.abs(np.subtract(arr, moving_median(arr)))
    return diff >= tol * np.percentile(diff, frac)


def sample_line_axes(shape):
    """Locate sample and line axes.

    Raises
    ------
    TypeError
        If the shape provided is smaller than 2.
    ValueError
        If none of the axes has 352 or 256 elements.

    """
    if len(shape) < 2:
        raise TypeError(f'Shape must be at least 2: {shape}')

    axes = list(range(len(shape)))

    if 352 in shape:
        axes.pop(shape.index(352))
        return tuple(axes)

    if 256 in shape:
        axes.pop(shape.index(256))
        return tuple(axes)

    raise ValueError(f'Band axis not found in shape {shape}.')


def median_spectrum(spectra):
    """Extract the median spectrum from a collection of spectra."""
    return np.median(spectra, axis=sample_line_axes(np.shape(spectra)))


def ir_multiplexer(spectrum):
    """Slit spectrum in IR in each multiplexer.

    If multiples spectrum are provided, the median
    spectrum will be extracted.

    Parameters
    ----------
    spectrum: list or numpy.ndarrray
        Input (VIS+IR) or (IR) spectrum.

    Returns
    -------
    numpy.ndarrray
        Multipler 1 spectrum.
    numpy.ndarrray
        Multipler 2 spectrum.

    Raises
    ------
    ValueError
        If the spectrum provided don't have the correct dimension.

    See Also
    --------
    :py:func:`median_spectrum`


    """
    if np.ndim(spectrum) == 1:
        if len(spectrum) == 352:
            return spectrum[96::2], spectrum[97::2]

        if len(spectrum) == 256:
            return spectrum[::2], spectrum[1::2]

    if np.ndim(spectrum) in [2, 3]:
        return ir_multiplexer(median_spectrum(spectrum))

    raise ValueError(f'Invalid spectrum dimension: `{np.shape(spectrum)}`.')


def ir_hot_pixels(spectrum, frac=95, tol=2.5):
    """Find hot pixel in IR spectra.

    The detection of hot pixel is done independantly
    on each IR multiplexer.
    If multiples spectrum are provided, the median
    spectrum will be use to used to locate the hot pixels.

    Parameters
    ----------
    spectrum: list or numpy.ndarrray
        Input (VIS+IR) or (IR) spectra.
    frac: float, optional
        Apriori fraction of valid pixels (95 % by default)
    tol: flat, optional
        Detection thresold criteria (2.5 by default)

    Returns
    -------
    list
        Sorted list of the channel(s) with hot pixels.

    See Also
    --------
    :py:func:`ir_multiplexer`
    :py:func:`is_hot_pixel`

    """
    # Split IR spectrum in each multiplexer
    ir_spec_1, ir_spec_2 = ir_multiplexer(spectrum)

    return np.sort(np.hstack([
        CHANNELS[96::2][is_hot_pixel(ir_spec_1, frac=frac, tol=tol)],
        CHANNELS[97::2][is_hot_pixel(ir_spec_2, frac=frac, tol=tol)],
    ])).astype(int)
