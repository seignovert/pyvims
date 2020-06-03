"""Image projection module."""

import numpy as np


def index(img, lon_w, lat):
    """Convert geographic coordinates as image coordinates.

    Parameters
    ----------
    img: 2d-array
        2D geol map image centered at 180°.
    lon_w: float or array
        Point west longitude(s).
    lat: float or array
        Point latitude(s).

    Returns
    -------
    int or array, int or array
        Array closest (j, i) coordinates on the image.

    """
    h, w = np.shape(img)[:2]

    i = np.round(np.multiply(-1, lon_w) % 360 * w / 360).astype(int)
    j = np.round(np.subtract(90, lat) * h / 180).astype(int)

    if np.ndim(lon_w) == 0:
        if i >= w or np.isnan(lon_w):
            i = w - 1
        if np.isnan(lat):
            j = h - 1
    else:
        i[(i >= w) | np.isnan(lon_w)] = w - 1
        j[(j >= h) | np.isnan(lat)] = h - 1

    return j, i
