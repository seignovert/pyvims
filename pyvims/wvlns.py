"""VIMS wavelength module."""

import numpy as np

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
