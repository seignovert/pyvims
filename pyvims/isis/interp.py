"""Interpolation module."""

import numpy as np

try:
    from matplotlib.path import Path
except ImportError:
    raise ImportError('Matplotlib module not found.')

try:
    from scipy.interpolate import griddata
except ImportError:
    raise ImportError('Scipy module not found.')


def _linspace(x0, x1, res, n=1):
    """Interpolation linspace.

    Parameters
    ----------
    x0: float
        Start point value.
    x1: float
        End point value.
    res: float:
        Pixel nominal resolution.
    n: int, optional
        Scaling factor.

    Returns
    -------
    np.array
        Interpolation points list.

    """
    nx = n * int(np.ceil((x1 - x0) / res))
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


def ortho_interp(xy, data, res, contour=False, n=10, method='cubic'):
    """Interpolat data in orthographic projection.

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
    n: int, optional
        Scaling factor.
    method: str, optional
        Interpolation method

    Returns
    -------
    np.array
        Interpolated data.

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

    x = _linspace(x0, x1, res, n)
    y = _linspace(y0, y1, res, n)
    X, Y = np.meshgrid(x, y)
    grid = (X, Y)

    z = griddata(pts, values, grid, method=method)

    if is_contour:
        z = np.ma.array(z, mask=_mask(grid, contour))

    return z, grid, _extent(x, y)


def _cross_180(lons, dlon=180):
    """Find the location of contour segment crossing the change of date meridian.

    Note
    ----
    The order is reverse to append new data
    without modifying the cross index.

    """
    i = np.arange(np.size(lons) - 1)
    return i[np.abs(lons[1:] - lons[:-1]) > dlon][::-1]


def c_equi(contour, sc_lat, dlon=180):
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
        frac = np.abs(180 - (clon[i] % 360)) / np.abs(clon[i+1] % 360 - clon[i] % 360)
        edge = 180 * np.sign(clon[i])
        lat = (clat[i+1] - clat[i]) * frac + clat[i]
        clon = np.insert(clon, i+1, [edge, edge, -edge, -edge])
        clat = np.insert(clat, i+1, [lat, pole, pole, lat])

    return clon, clat
