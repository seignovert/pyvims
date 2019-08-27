"""Cube projection module."""

import numpy as np

from .interp import cube_interp
from .vectors import deg180


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
        Orthograpahic projected point on X-axis.
    y: float or np.array
        Orthograpahic projected point on Y-axis.
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
    """VIMS cube orthographicly projected on the median FOV.

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


def _cross_180(lons, dlon=180):
    """Find the location of contour segment crossing the change of date meridian.

    Note
    ----
    The order is reverse to append new data
    without modifying the cross index.

    """
    i = np.arange(np.size(lons) - 1)
    return i[np.abs(lons[1:] - lons[:-1]) > dlon][::-1]


def equi_contour(contour, sc_lat, dlon=180):
    """Extented contour in equirectangular geometry.

    Parameters
    ----------
    contour: np.array
        Longitude and latitude contour coordinates.
    sc_lat: float
        Sub-spacecradt latitude.

    Returns
    -------
    np.array
        Wrapped contour(s) in equirectangular projection.

    """
    clon, clat = contour
    pole = 90 * np.sign(sc_lat)

    for i in _cross_180(clon):
        frac = np.abs(180 - (clon[i] % 360)) / \
            np.abs(clon[i+1] % 360 - clon[i] % 360)
        edge = 180 * np.sign(clon[i])
        lat = (clat[i+1] - clat[i]) * frac + clat[i]
        clon = np.insert(clon, i+1, [edge, edge, -edge, -edge])
        clat = np.insert(clat, i+1, [lat, pole, pole, lat])

    return clon, clat


def equi_grid(glon, glat, npix=1440):
    """Create optimize equirectangular grid.

    Parameters
    ----------
    glon: np.array
        Ground longitude.
    glat: np.array
        Ground latitude.
    npix: int, optional
        Maximum mumber of pixel in X-axis (or half in Y-axis)

    Returns
    -------
    (np.array, np.array)
        Equirectangular grid.
    list
        Equirectangular extent for pyplot.

    """
    x0, y0 = np.floor(np.min([glon, glat], axis=1))
    x1, y1 = np.ceil(np.max([glon, glat], axis=1))

    pix = (x1 - x0) / npix if x1 - x0 > y1 - y0 else (y1 - y0) / (npix / 2)

    x = np.arange(x0 + .5 * pix, x1, pix)
    y = np.arange(y0 + .5 * pix, y1, pix)

    X, Y = np.meshgrid(x, y)
    grid = (X, Y)
    extent = [x0, x1, y1, y0]

    return grid, extent
