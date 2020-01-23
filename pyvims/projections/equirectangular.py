"""Equirectangular projection module."""

import numpy as np

from scipy.interpolate import griddata

from .orthographic import ortho_grid
from ..interp import cube_interp, mask
from ..vectors import areaquad


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
    """Extended contour in equirectangular geometry.

    Parameters
    ----------
    contour: np.array
        Longitude and latitude contour coordinates.
    sc_lat: float
        Sub-spacecraft latitude.

    Returns
    -------
    np.array
        Wrapped contour(s) in equirectangular projection.

    """
    clon, clat = contour
    pole = 90 * np.sign(sc_lat)

    for i in _cross_180(clon):
        frac = np.abs(180 - (clon[i] % 360)) / \
            np.abs(clon[i + 1] % 360 - clon[i] % 360)
        edge = 180 * np.sign(clon[i])
        lat = (clat[i + 1] - clat[i]) * frac + clat[i]
        clon = np.insert(clon, i + 1, [edge, edge, -edge, -edge])
        clat = np.insert(clat, i + 1, [lat, pole, pole, lat])

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
        Maximum number of pixel in X-axis (or half in Y-axis)

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
        Maximum number of pixel in X-axis (or half in Y-axis)
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
    m = mask(grid, ctn)

    if np.ndim(gz_interp) == 3:
        z_mask = np.moveaxis([
            gz_interp[:, :, 0],
            gz_interp[:, :, 1],
            gz_interp[:, :, 2],
            255 * np.int8(~m)
        ], 0, 2)
    else:
        z_mask = np.ma.array(gz_interp, mask=m)

    return z_mask, grid, extent, ctn


def equi_cube(c, index, ppd=4, n=512, res_min=1, interp='cubic'):
    """VIMS cube equirectangular projected.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to interpolate.
    index: int, float, str, list, tuple
        VIMS band or wavelength to plot.
    ppd: int
        Number of pixels per degree
    n: int, optional
        Number of pixel for the grid interpolation.
    interp: str, optional
        Interpolation method
    res_min: float, optional
        Minimal resolution

    """
    # Pixel data
    data = c[index]

    # Pixel positions on the FOV tangent plane
    pixels = c.ortho

    # Contour positions on the FOV tangent plane
    contour = c.cortho

    # Orthographic resolution
    res = max(np.min(np.max(contour, axis=1) - np.min(contour, axis=1)) / n, res_min)

    # Equirectangular resolution at the equator
    npix = 360 * ppd

    # Sub-spacecraft location for initial orthographic projection
    sc = c.sc

    # Target radius for initial orthographic projection
    r = c.target_radius

    # Interpolate data (with mask)
    return equi_interp(pixels, data, res, contour, sc, r, npix=npix, method=interp)


def pixel_area(img, r=1):
    """Pixel area in equirectangular projection.

    Parameters
    ----------
    img: array
        2D or 3D image array in equirectangular projection.
    r: float, optional
        Planet radius [km].

    Returns
    -------
    array
        Pixel area [km^2]

    Note
    ----
    Broadcast array in 2D:
        https://stackoverflow.com/a/27593639

    """
    h, w = np.shape(img)[:2]
    dlon = 360 / w
    lats = np.linspace(-90, 90, h + 1)
    area = areaquad(0, lats[:-1], dlon, lats[1:], r=r)
    return np.broadcast_arrays(np.ones((1, w)), area[..., None])[1]
