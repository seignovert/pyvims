"""Path 3D module."""

import numpy as np

from matplotlib.path import Path


class Path3D(Path):
    """Extend matplotlib 2D Path object with altitude attribute.

    Parameters
    ----------
    vertices: Nx2 array
        Path vertices.
    codes: N array
        Path codes.
    alt: N array
        Point altitude [km].

    Raises
    ------
    ValueError
        If the altitude array does not have the same length
        as the vertices array.

    """

    def __init__(self, *args, alt=None, **kwargs):
        super().__init__(*args, **kwargs)

        if alt is not None and \
                (np.ndim(alt) == 0 or len(self.vertices) != np.shape(alt)[0]):
            raise ValueError('Altitude array must have the same length as the vertices.')

        self.alt = alt
