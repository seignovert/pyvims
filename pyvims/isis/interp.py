"""Interpolation module."""

from matplotlib.path import Path

import numpy as np

from scipy.interpolate import griddata

from .img import rgb


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


def mask(grid, contour):
    """Mask data outside the contour.

    Parameters
    ----------
    grid: np.array
        X-Y grid of pixels.
    contour: np.array
        X-Y coordinates of the contour

    Returns
    -------
    np.array
        Boolean array of all the pixels ouside the contour.

    """
    x, y = grid
    pts = np.hstack((x.reshape(-1, 1), y.reshape(-1, 1)))

    polygon = Path(np.transpose(contour))
    mask = polygon.contains_points(pts).reshape(np.shape(x))

    return ~mask


def _interp_1d(pts, data, grid, method='cubic', is_contour=True):
    """1D data grid interpolation."""
    values = np.array(data).flatten()

    if is_contour:
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

    # If some data are mask, they are removed before the interpolation.
    if isinstance(pts, np.ma.core.MaskedArray):
        m = np.ma.getmask(pts[:, 0])
        pts = pts[~m, :]
        values = values[~m]

    return griddata(pts, values, grid, method=method)


def cube_interp(xy, data, res, contour=False, method='cubic'):
    """Interpolate cube data.

    Parameters
    ----------
    xy: np.array
        2D points location (X and Y).
    data: np.array
        2D data values.
    res: float
        Pixel resolution (for grid interpolation).
    contour: np.array, optional
        Pixels contour location.
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

    Raises
    ------
    ValueError
        If the data provided are 3D but without 3 backplanes (R, G, B).

    """
    pts = np.ma.reshape(xy, (2, int(np.size(xy) / 2))).T
    is_contour = isinstance(contour, (list, tuple, np.ndarray))

    if is_contour:
        pts = np.ma.vstack([pts, np.transpose(contour)])

    x0, y0 = np.min(pts, axis=0)
    x1, y1 = np.max(pts, axis=0)

    x = _linspace(x0, x1, res)
    y = _linspace(y0, y1, res)
    xx, yy = np.meshgrid(x, y)
    grid = (xx, yy)

    kwargs = {'method': method, 'is_contour': is_contour}

    if np.ndim(data) == 3:
        if np.shape(data)[-1] == 3:
            r = _interp_1d(pts, data[:, :, 0], grid, **kwargs)
            g = _interp_1d(pts, data[:, :, 1], grid, **kwargs)
            b = _interp_1d(pts, data[:, :, 2], grid, **kwargs)
            z = rgb(r, g, b)
        else:
            raise ValueError('3D data array can only have 3 planes (R, G, B), '
                             f'{np.shape(data)[-1]} planes were provided.')

    else:
        z = _interp_1d(pts, data, grid, **kwargs)

    if is_contour:
        m = mask(grid, contour)

        if np.ndim(data) == 3:
            z = np.moveaxis([z[:, :, 0], z[:, :, 1], z[:, :, 2], 255 * np.int8(~m)], 0, 2)
        else:
            z = np.ma.array(z, mask=m)

    return z, grid, _extent(x, y)
