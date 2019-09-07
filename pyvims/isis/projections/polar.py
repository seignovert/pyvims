"""Polar equidistante projection module."""

import numpy as np

from ..interp import cube_interp_filled


def xy(lon, lat):
    """Convert longitude / latitude points on the pole."""
    rad_lon = np.radians(lon)
    c_lon, s_lon = np.cos(rad_lon), np.sin(rad_lon)
    r = 90 - np.asarray(lat)
    return np.array([-r * s_lon, r * c_lon])


def lonlat(x, y):
    """Convert polar projected point on the pole to latitutde and longitude."""
    lon = np.degrees(np.arctan2(x, -y))
    lat = 90 - np.sqrt(np.sum(np.power([x, y], 2), axis=0))
    return lon, lat


def polar_proj(lon, lat, n_pole=True, dlat=180):
    """Pixels position in Polar projection.

    Parameters
    ----------
    lon: np.array
        Pixel WEST longitude (degree).
    lat: np.array
        Pixel NORTH latitude (degree).
    n_pole: bool, optional
        Set to ``TRUE`` to project on the North Pole.
    dlat: float, optional
        Maximum latitude distance to the pole.

    Returns
    -------
    np.array
        Pixels X and Y positions in polar projection.

    """
    x, y = xy(lon, lat) if n_pole else xy(lon, -lat)

    mask_lat = (90 - lat > dlat) if n_pole else (90 + lat > dlat)
    mask = mask_lat | np.ma.getmask(lon) | np.ma.getmask(lat)

    return np.ma.array([x, y], mask=[mask, mask])


def polar_grid(grid):
    """Interpolated polar grid.

    Parameters
    ----------
    grid: np.array
        Interpolated grid.

    Returns
    -------
    np.array
        Grid lon/lat coordinates.

    """
    return lonlat(*grid)


def polar_interp(xy, data, contour, n=512, method='cubic'):
    """Pixel interpolation in polar projection.

    Parameters
    ----------
    pixels: np.array
        Pixels X/Y positions.
    data: np.array
        2D/3D data pixels values.
    contour: np.array
        Contour X/Y positions.
    n: int, optional
        Number of pixel for the grid interpolation.
    method: str, optional
        Interpolation method

    Returns
    -------
    np.array
        Interpolated data.
    np.array
        Interpolated grid.
    list
        Data extent for pyplot.

    """
    # Plane resolution
    res = np.min(np.max(contour, axis=1) - np.min(contour, axis=1)) / n

    # Polar interpolation filled within the contour
    return cube_interp_filled(xy, data, res, contour, method=method)


def polar_cube(c, index, n=512, interp='cubic'):
    """VIMS cube polar projected.

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

    # Choose which pole to display
    n_pole = c.sc_lat > 0

    # Pixel positions in polar projection
    pixels = polar_proj(c.ground_lon, c.ground_lat, n_pole=n_pole)

    # Contour positions in polar projection
    contour = polar_proj(*c.clonlat, n_pole=n_pole)

    # Interpolate data (with mask)
    z, grid, extent = polar_interp(pixels, data, contour, n=n, method=interp)

    return z, grid, extent, pixels, contour, n_pole
