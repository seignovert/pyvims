"""VIMS image module."""

import numpy as np


def _clip(img, imin=None, imax=None):
    """Clip image plane from 0 to 255 between imin and imax.

    Parameters
    ----------
    img: np.array
        Input 2D data plane.
    imin: float, optional
        Custom minimum clipping value.
    imax: float, optional
        Custom maximum clipping value.

    Returns
    -------
    np.array
        8 bits clipped image plane.

    """
    if imin is None:
        imin = np.nanmin(img)

    if imax is None:
        imax = np.nanmax(img)

    return np.uint8(np.clip(255 * (img - imin) / (imax - imin), 0, 255))


def rgb(r, g, b):
    """Create RGB 8 bits image from 3 channels.

    Parameters
    ----------
    r: np.array
        Red image plane data.
    g: np.array
        Green image plane data.
    b: np.array
        Blue image plane data.

    Returns
    -------
    np.array
        8 bits RGB image.

    """
    return np.moveaxis(np.vstack([
        [_clip(r)], [_clip(g)], [_clip(b)]
    ]), 0, 2)
