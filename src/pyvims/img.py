"""VIMS image module."""

import numpy as np

import matplotlib.pyplot as plt


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


def rgb(r, g, b, imin=None, imax=None):
    """Create RGB 8 bits image from 3 channels.

    Parameters
    ----------
    r: np.array
        Red image plane data.
    g: np.array
        Green image plane data.
    b: np.array
        Blue image plane data.
    imin: float, optional
        Custom minimum clipping value.
    imax: float, optional
        Custom maximum clipping value.

    Returns
    -------
    np.array
        8 bits RGB image.

    """
    return np.moveaxis(np.vstack([
        [_clip(r, imin=imin, imax=imax)],
        [_clip(g, imin=imin, imax=imax)],
        [_clip(b, imin=imin, imax=imax)]
    ]), 0, 2)


def rgba(r, g, b, a):
    """Create RGBA 8 bits image from 4 channels.

    Parameters
    ----------
    r: np.array
        Red image plane data.
    g: np.array
        Green image plane data.
    b: np.array
        Blue image plane data.
    a: np.array
        Alpha image plane data.

    Returns
    -------
    np.array
        8 bits RGBA image.

    """
    return np.moveaxis(np.vstack([
        [_clip(r)], [_clip(g)], [_clip(b)], [_clip(a)]
    ]), 0, 2)


def save_img(fname, data, ir_hr=False, npix=256, quality=65, interp='bicubic'):
    """Save JPG image from data array.

    Parameters
    ----------
    fname: str
        Output filename.
    data: np.array
        Input data array.
    ir_hr: bool, optional
        Infrared high resolution aspect ratio (before projection).
    npix: int, optional
        Number of pixels in the largest dimension.
    quality: int, optional
        JPEG compression quality.
    interp: str, optional
        Pyplot interpolation method.

    """
    if np.ndim(data) == 2:
        h, w = np.shape(data)
    elif np.ndim(data) == 3:
        h, w, _ = np.shape(data)
    else:
        raise ValueError('Data must be a 2D or 3D array.')

    extent = [0, w, h, 0]

    if ir_hr:
        w /= 2

    if w >= h:
        nx = 1
        ny = h / w
    else:
        nx = w / h
        ny = 1

    fig = plt.figure(frameon=False, dpi=npix, figsize=(nx, ny))

    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    ax.imshow(data, extent=extent, cmap='gray', interpolation=interp)

    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    if ir_hr:
        ax.set_aspect(2)

    fig.savefig(fname, quality=quality, bbox_inches='tight', pad_inches=0)
    plt.close()
