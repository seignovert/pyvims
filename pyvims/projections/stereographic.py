"""Polar stereographic projection module."""

import numpy as np

from ..interp import cube_interp_filled


def r_stereo(lat, n_pole=True):
    """Convert radius for stereo projection."""
    s = 1 if n_pole else -1
    return 1 / np.tan(np.radians(np.add(90, s * lat)) / 2)


def inv_r_stereo(r, n_pole=True):
    """Convert stereo radius in latitude."""
    return np.degrees(2 * np.arctan2(1, r)) - 90


def stereo_scale(data, lat_min, n_pole=True):
    """Get image polar stereographic center and scaling.

    Parameters
    ----------
    data: np.array
        Image in polar stereographic projection.
    lat_min: float
        Border minimum latitude.
    n_pole: bool, optional
        Set to ``TRUE`` to project on the North Pole.

    Returns
    -------
    float
        Position of the center.
    float
        Radius scaling factor.

    Raises
    ------
    ValueError
        If the image is not squared.

    Notes
    -----
    The image need to be centered and squared first.

    """
    shape = np.shape(data)
    if shape[0] != shape[1]:
        raise ValueError('The image is not square')
    r = r_stereo(lat_min, n_pole=n_pole)
    return (shape[0] - 1) / 2, shape[0] / (2 * r)


def xy(lon, lat, center=(0, 0), scale=1, n_pole=True):
    """Convert geographic coordinates into image coordinates.

    Parameters
    ----------
    lon: float
        Longitude positive west (degree).
    lat: float
        Latitude positive north (degree).
    center: float, optional
        Pixel position of the center of the stereographic
        polar projected image.
    scale: float, optional
        Polar projection radius scaling factor.
    n_pole: bool, optional
        Set to ``TRUE`` to project on the North Pole.

    Returns
    -------
    float, float
        Pixel position in the stereographic polar
        projected coordinates.

    """
    r_lon = np.radians(lon)
    c_lon, s_lon = np.cos(r_lon), np.sin(r_lon)
    r = r_stereo(lat, n_pole=n_pole) * scale
    return center[0] - r * s_lon, center[1] + r * c_lon * (1 if n_pole else -1)


def lonlat(x, y, center=(0, 0), scale=1, n_pole=True):
    """Convert geographic coordinates into image coordinates.

    Parameters
    ----------
    x: float
        Pixel sample position.
    y: float
        Pixel line position.
    center: float, optional
        Pixel position of the center of the stereographic
        polar projected image.
    scale: float, optional
        Polar projection radius scaling factor.

    Returns
    -------
    float, float
        Longitude (west) and latitude (degree).

    """
    s, l = center[0] - x, y - center[1]
    r = np.sqrt(np.sum(np.power([s, l], 2), axis=0)) / scale
    lon = np.degrees(np.arctan2(s, l))
    lat = inv_r_stereo(r, n_pole=n_pole)
    return lon, lat


def stereo_grid(grid, center=(0, 0), scale=1):
    """Interpolated polar stereographic grid.

    Parameters
    ----------
    grid: np.array
        Interpolated grid.
    center: float, optional
        Pixel position of the center of the stereographic
        polar projected image.
    scale: float, optional
        Polar projection radius scaling factor.


    Returns
    -------
    np.array
        Grid lon/lat coordinates.

    """
    return lonlat(*grid)


def stereo_interp(xy, data, contour, n=512, method='cubic'):
    """Pixel interpolation in polar stereographic projection.

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


def stereo_cube(c, index, n=512, interp='cubic', center=(0, 0), scale=1):
    """VIMS cube polar stereographic projected.

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
    center: float, optional
        Pixel position of the center of the stereographic
        polar projected image.
    scale: float, optional
        Polar projection radius scaling factor.

    """
    # Pixel data
    data = c[index]

    # Choose which pole to display
    n_pole = c.sc_lat > 0

    # Pixel positions in polar projection
    pixels = xy(c.ground_lon, c.ground_lat, center=center, scale=scale, n_pole=n_pole)

    # Contour positions in polar projection
    contour = xy(*c.clonlat, center=center, scale=scale, n_pole=n_pole)

    # Interpolate data (with mask)
    z, grid, extent = stereo_interp(pixels, data, contour, n=n, method=interp)

    return z, grid, extent, pixels, contour, n_pole, stereo_grid(grid)
