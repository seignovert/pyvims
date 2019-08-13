"""Cube projection module."""

import numpy as np


def ortho(lon, lat, lon_0=0, lat_0=0, r=1, alt=None):
    """Orthographic projection centered on (lon_0, lat_0).

    Parameters
    ----------
    lon: float or np.array
        Points west longitude (degrees).
    lat: float or np.array
        Points north latitude (degrees).
    lon_0: float or np.array
        Centered longitude (degrees).
    lat_0: float or np.array
        Centered latitude (degrees).
    alt: float or np.array, optional
        Planet radius.
    alt: float or np.array, optional
        Points altitude (same units as r).

    Returns
    -------
    (np.array, np.array)
        Projection coordinates.

    """
    dlambda, phi = np.radians([lon_0 - lon, lat])
    phi_0 = np.radians(lat_0)

    c_lambda, c_phi = np.cos([dlambda, phi])
    s_lambda, s_phi = np.sin([dlambda, phi])
    c_phi_0 = np.cos(phi_0)
    s_phi_0 = np.sin(phi_0)

    x = r * c_phi * s_lambda
    y = r * (c_phi_0 * s_phi - s_phi_0 * c_phi * c_lambda)
    cos_c = s_phi_0 * s_phi + c_phi_0 * c_phi * c_lambda

    if alt is None:
        mask = cos_c < 0 | np.ma.getmask(lon) | np.ma.getmask(lat)
    else:
        x *= 1 + alt / r
        y *= 1 + alt / r
        mask = cos_c < 0

    return np.ma.array([x, y], mask=[mask, mask])
