"""Equirectangular projection module."""

import numpy as np

from scipy.interpolate import griddata

from .orthographic import ortho_grid
from ..interp import cube_interp, _mask


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


def equi_interp(xy, data, res, contour, sc, r, npix=1440, method='cubic'):
    """Interpolate data in equirectangular projection.

    Parameters
    ----------
    xy: np.array
        2D orthographic points location (X and Y).
    data: np.array
        2D data values.
    res: float
        Pixel resolution (for grid interpolation).
    contour: np.array
        Pixels contour location in orthographic projection.
    sc: (float, float)
        Sub-spacecraft point longitude and latitude.
    r: float
        Target radius (km).
    npix: int, optional
        Maximum mumber of pixel in X-axis (or half in Y-axis)
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
    # Orthographic interpolation
    z, grid, extent = cube_interp(xy, data, res, contour, method=method)

    # Orthographic geographic pixels coordinates
    o_lon, o_lat, o_alt = ortho_grid(*grid, *sc, r)
    c_lon, c_lat, _ = ortho_grid(*contour, *sc, r)

    # Interpolated ground pixels (remove limb pixel where altitude > 0)
    ground = o_alt < 1e-6
    glon, glat, gz = o_lon[ground], o_lat[ground], z[ground]

    # Equirectangular contour
    ctn = equi_contour((c_lon, c_lat), sc[1])

    # Equirectangular grid
    grid, extent = equi_grid(*ctn, npix=npix)

    # Interpolate the equirectangular data with the nearest value
    gz_interp = griddata((glon, glat), gz, grid, method='nearest')

    # Create mask for pixels outside the contour
    mask = _mask(grid, ctn)

    return np.ma.array(gz_interp, mask=mask), grid, extent
