"""Globe projection module."""

import numpy as np

from .ortho import Orthographic
from .img import index


def globe(img, lon_w_0=0, lat_0=0, npt=1024):
    """Project image on a globe.

    Parameters
    ----------
    lon_w_0: float, optional
        Center west longitude.
    lat_0: float, optional
        Center latitude (North Pole by default).
    npt: int, optional
        Number of point in the image.

    Returns
    -------
    numpy.array
        Projected image on a globe.

    """
    x = np.linspace(-1, 1, npt)

    s = np.broadcast_to(x, (npt, npt))
    l = np.broadcast_to(x[::-1, None], (npt, npt))

    ortho = Orthographic(lon_w_0=lon_w_0, lat_0=lat_0)

    lon_w, lat = ortho(s, l, invert=True)
    im = img[index(img, lon_w, lat)]

    # Discard invalid points
    fill_value = 255 if img.dtype == np.uint8 else np.nan
    im[np.isnan(lon_w) | np.isnan(lat)] = fill_value

    return im
