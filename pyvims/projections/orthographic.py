"""Orthographic projection module."""

import numpy as np

from ..vectors import deg180
from ..interp import cube_interp


def ortho_proj(lon, lat, lon_0=0, lat_0=0, r=1, alt=None):
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
    r: float or np.array, optional
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


def ortho_grid(x, y, lon_0=0, lat_0=0, r=1):
    """Convert orthographic coordinates to planetocentric coordinates.

    Parameters
    ----------
    x: float or np.array
        Orthographic projected point on X-axis.
    y: float or np.array
        Orthographic projected point on Y-axis.
    lon_0: float or np.array
        Orthographic centered longitude (degrees).
    lat_0: float or np.array
        Orthographic centered latitude (degrees).
    r: float or np.array, optional
        Planet radius.

    Returns
    -------
    np.array
        Planetocentric coordinates.

    """
    lambda_0, phi_0 = np.radians([lon_0, lat_0])
    c_lambda_0, c_phi_0 = np.cos([lambda_0, phi_0])
    s_lambda_0, s_phi_0 = np.sin([lambda_0, phi_0])

    rho = np.sqrt(np.power(x, 2) + np.power(y, 2))
    c = np.arcsin(np.min([np.ones(np.shape(rho)), rho / r], axis=0))
    c_c, s_c = np.cos(c), np.sin(c)

    phi = np.arcsin(c_c * s_phi_0 + y / rho * s_c * c_phi_0)
    lambd = lambda_0 - np.arctan2(x * s_c, rho * c_c * c_phi_0 - y * s_c * s_phi_0)

    lon, lat = np.degrees([lambd, phi])
    alt = r * (np.max([np.ones(np.shape(rho)), rho / r], axis=0) - 1)
    return deg180(lon), lat, alt


def ortho_cube(c, index, n=512, interp='cubic'):
    """VIMS cube orthographically projected on the median FOV.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to interpolate.
    index: int, float, str, list, tuple
        VIMS band or wavelength to plot.
    n: int, optional
        Number of pixel for the grid interpolation.
    interp: str, optional
        Interpolation method

    """
    # Pixel data
    data = c[index]

    # Pixel positions on the FOV tangent plane
    pixels = c.ortho

    # Contour positions on the FOV tangent plane
    contour = c.cortho

    # Plane resolution
    res = np.min(np.max(contour, axis=1) - np.min(contour, axis=1)) / n

    # Interpolate data (with mask)
    z, grid, extent = cube_interp(pixels, data, res=res, contour=contour, method=interp)

    # Coordinates of the interpolated grid
    o_grid = ortho_grid(*grid, *c.sc, c.target_radius)

    return z, grid, extent, pixels, contour, o_grid
