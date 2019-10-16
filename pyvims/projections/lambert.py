"""Lambert azimuthal equal-area projection module."""

import numpy as np


def xy(lon, lat, lon_0=0, lat_0=0, r=1):
    """Convert longitude and latitude in Lambert azimuthal projection.

    Parameters
    -----------
    lon: float or np.array
        Point(s) west longitude (degree)
    lat: float or array
        Point(s) latitude (degree)
    lon_0: float, optional
        Center west longitude (degree)
    lat_0: float, optional
        Center latitude (degree)
    r: float, optional
        Planet radius.

    Returns
    -------
    np.array
        Pixels X and Y positions in Lambert azimuthal.

    """
    dlambda, phi = np.radians([lon_0 - lon, lat])
    phi_0 = np.radians(lat_0)

    c_dlambda, c_phi = np.cos([dlambda, phi])
    s_dlambda, s_phi = np.sin([dlambda, phi])
    c_phi_0 = np.cos(phi_0)
    s_phi_0 = np.sin(phi_0)

    k = np.sqrt(2 / (1 + s_phi_0 * s_phi + c_phi_0 * c_phi * c_dlambda))
    x = r * k * c_phi * s_dlambda
    y = r * k * (c_phi_0 * s_phi - s_phi_0 * c_phi * c_dlambda)

    if np.ma.getmask(lon).any() or np.ma.getmask(lat).any():
        mask = np.ma.getmask(lon) | np.ma.getmask(lat)
        return np.ma.array([x, y], mask=[mask, mask])

    return np.array([x, y])
