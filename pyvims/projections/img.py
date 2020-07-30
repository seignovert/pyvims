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


def bg_pole(img, proj, lat_1=60, n=1024):
    """Polar projection of a background map.

    Parameters
    ----------
    img: 2d-array
        2D geol map image centered at 180°.
    proj: pyvims.projections.GroundProjection
        Polar ground projection (``Stereographic`` in most cases).
    lat_1: float
        Cut-off latitude.
    n: int
        Number of point in the image.

    Returns
    -------
    array
        Projected background image.
    array
        Matplotlib image extent.

    """
    r, _ = proj(-90, lat_1)
    x = np.broadcast_to(np.linspace(-r, r, n), (n, n))
    y = np.broadcast_to(np.linspace(-r, r, n)[::-1, None], (n, n))
    mask = x**2 + y**2 < r**2
    extent = [-r, r, -r, r]

    if img.dtype == np.uint8:
        mask = (255 * mask).astype(np.uint8)

    lon_w, lat = proj(x, y, invert=True)

    im = img[index(img, lon_w, lat)]

    if np.ndim(img) == 2:
        im = np.moveaxis(np.stack([im, im, im, mask]), 0, 2)
    else:
        im = np.moveaxis(np.stack([im[:, :, 0], im[:, :, 1], im[:, :, 2], mask]), 0, 2)

    return im, extent
