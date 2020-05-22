"""Interpolation module."""

from matplotlib.path import Path

import numpy as np

from scipy.interpolate import griddata

from .img import rgb, rgba


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


def _grid(pts, res):
    """Create grid based on points.

    Parameters
    ----------
    pts: list
        List of 2D points used for the grid.
    res: float
        Grid resolution.

    Returns
    -------
    np.array
        Meshgrid based on points.

    """
    (x0, y0), (x1, y1) = np.min(pts, axis=0), np.max(pts, axis=0)

    x = _linspace(x0, x1, res)
    y = _linspace(y0, y1, res)
    xx, yy = np.meshgrid(x, y)

    return (xx, yy), _extent(x, y)


def _flat(arr, mask=False):
    """Flatten array on the first column."""
    if np.ndim(arr) == 2:
        farr = np.asarray(arr).flatten()

    elif np.ndim(arr) == 3:
        s = np.shape(arr)
        farr = np.ma.reshape(arr, (s[0], int(np.size(arr) / s[0])))

    else:
        raise ValueError(f'Array dimension invalid: {np.ndmin(arr)}')

    if isinstance(mask, (list, tuple, np.ndarray)):
        return np.ma.array(farr, mask=mask)

    return farr


def _interp_1d(pts, data, grid, method='cubic', is_contour=True):
    """1D data grid interpolation."""
    values = _flat(data)

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
    pts = _flat(xy).T
    is_contour = isinstance(contour, (list, tuple, np.ndarray))

    if is_contour:
        pts = np.ma.vstack([pts, np.transpose(contour)])

    grid, extent = _grid(pts, res)

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

    return z, grid, extent


def cube_interp_filled(xy, data, res, contour, method='cubic'):
    """Interpolate cube data within a contour.

    The missing data into the contour are filled with the nearest value.

    Parameters
    ----------
    xy: np.array
        2D points location (X and Y).
    data: np.array
        2D data values.
    res: float
        Pixel resolution (for grid interpolation).
    contour: np.array
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

    """
    # Create grid based on contour size and resolution.
    grid, extent = _grid(np.transpose(contour), res)

    # Remove masked data
    x, y = xy
    if isinstance(x, np.ma.core.MaskedArray):
        xx, yy, dd = x[~x.mask], y[~y.mask], data[~x.mask]
    else:
        xx, yy, data = x, y, data

    # Cube interpolation without the contour
    z = griddata((xx, yy), dd, grid, method='cubic')

    # Cube nearest extrapolation
    nearest = griddata((xx, yy), dd, grid, method='nearest')

    # Fill the missing data
    missing = np.isnan(z)
    z[missing] = nearest[missing]

    # Create mask based on the contour
    m = mask(grid, contour)

    if np.ndim(data) == 3:
        # Add alpha channel outside the contour
        z = rgba(z[:, :, 0], z[:, :, 1], z[:, :, 2], np.int8(~m))
    else:
        # Mask the data outside the contour
        z = np.ma.array(z, mask=m)

    return z, grid, extent


def lin_interp(x, xp, fp):
    """Linear interpolation on array.

    Parameters
    ----------
    x: int, float or numpy.ndarray
        K positions to interpolate.
    xp: numpy.ndarray
        M data positions.
    fp: numpy.ndarray
        N x M data values.

    Returns
    -------
    numpy.ndarray
        K x N values linearly interpolated.

    Raises
    ------
    ValueError
        If any of the input positions is outside
        the interpolation range
    IndexError
        If the data

    Note
    ----
    Idea: https://stackoverflow.com/a/43775224

    """
    if np.min(x) < xp[0]:
        raise ValueError(f'Outside interpolation range: {np.min(x)} < min = {xp[0]}')

    if np.max(x) > xp[-1]:
        raise ValueError(f'Outside interpolation range: {np.max(x)} > max = {xp[-1]}')

    if np.ndim(fp) == 1:
        return np.interp(x, xp, fp)

    _xp, _fp = np.asarray(xp), np.asarray(fp)

    if _xp.shape[0] != _fp.shape[1]:
        raise IndexError(
            f'Invalid positions and values shapes: {_xp.shape} vs. {_fp.shape}')

    i = np.arange(_fp.shape[0])
    j = np.searchsorted(_xp, x) - 1
    d = (x - _xp[j]) / (_xp[j + 1] - _xp[j])

    if np.ndim(x) > 0:
        j, d = j[:, None], d[:, None]

    return (1 - d) * _fp[i, j] + d * _fp[i, j + 1]
