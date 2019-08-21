"""Interpolation module."""

from matplotlib.path import Path

import numpy as np

from scipy.interpolate import griddata

from .projection import equi_contour, equi_grid, ortho_grid


def _linspace(x0, x1, res):
    """Interpolation linspace.

    Parameters
    ----------
    x0: float
        Start point value.
    x1: float
        End point value.
    res: float:
        Pixel nominal resolution.

    Returns
    -------
    np.array
        Interpolation points list.

    """
    nx = int(np.ceil((x1 - x0) / res))
    return np.linspace(x0, x1, nx)


def _extent(x, y):
    """Get data extent for pyplot imshow.

    Parameters
    ----------
    x: list
        Data array on X-axis.
    y: list
        Data array on Y-axis.

    Returns
    -------
    [float, float, float, float]
        X and Y extent.

    """
    dx, dy = .5 * (x[1] - x[0]), .5 * (y[1] - y[0])
    return [x[0] - dx, x[-1] + dx, y[-1] + dy, y[0] - dy]


def _mask(grid, contour):
    """Mask data outside the contour."""
    x, y = grid
    pts = np.hstack((x.reshape(-1, 1), y.reshape(-1, 1)))

    polygon = Path(np.transpose(contour))
    mask = polygon.contains_points(pts).reshape(np.shape(x))

    return ~mask


def ortho_interp(xy, data, res, contour=False, method='cubic'):
    """Interpolate data in orthographic projection.

    Parameters
    ----------
    xy: np.array
        2D orthographic points location (X and Y).
    data: np.array
        2D data values.
    res: float
        Pixel resolution (for grid interpolation).
    contour: np.array, optional
        Pixels contour location in orthographic projection.
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
    pts = np.reshape(xy, (2, np.size(data))).T
    values = np.array(data).flatten()
    is_contour = isinstance(contour, (list, np.ndarray))

    if is_contour:
        pts = np.vstack([pts, np.transpose(contour)])
        values = np.hstack([
            values,
            data[0, 0],      # Top-Left corner
            data[0, :],      # Top edge
            data[0, -1],     # Top-Right corner
            data[:, -1],     # Right edge
            data[-1, -1],    # Bottom-Right corner
            data[-1, ::-1],  # Bottom edge
            data[-1, 0],     # Bottom-Left corner
            data[::-1, 0],   # Left edge
            data[0, 0],      # Top-Left corner
        ])

    x0, y0 = np.min(pts, axis=0)
    x1, y1 = np.max(pts, axis=0)

    x = _linspace(x0, x1, res)
    y = _linspace(y0, y1, res)
    X, Y = np.meshgrid(x, y)
    grid = (X, Y)

    z = griddata(pts, values, grid, method=method)

    if is_contour:
        z = np.ma.array(z, mask=_mask(grid, contour))

    return z, grid, _extent(x, y)


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
    z, grid, extent = ortho_interp(xy, data, res, contour, method=method)

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
