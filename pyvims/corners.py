"""VIMS pixel corners module."""

import numpy as np

from matplotlib.patches import PathPatch
from matplotlib.path import Path


CODES = {
    'corners': [Path.MOVETO] + [Path.LINETO] * 3 + [Path.CLOSEPOLY],
    'footprint': [Path.MOVETO] + [Path.LINETO] * 7 + [Path.CLOSEPOLY],
}

class VIMSPixelCorners:
    """VIMS corners object.

    Parameters
    ----------
    pixel: pyvims.VIMSPixel
        Parent VIMS cube pixel.

    """

    def __init__(self, pixel):
        self._pix = pixel

    def __str__(self):
        return f'{self._cube}-S{self.s}_L{self.l}-corners'

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> {self}',
            f'Sample: {self.s}',
            f'Line: {self.l}',
        ])

    @property
    def _cube(self):
        """Parent VIMS cube."""
        return self._pix._cube  # pylint: disable=protected-access

    @property
    def s(self):
        """Pixel sample position."""
        return self._pix.s

    @property
    def i(self):
        """Sample index value."""
        return self._pix.i

    @property
    def l(self):
        """Pixel lines position."""
        return self._pix.l

    @property
    def j(self):
        """Line index value."""
        return self._pix.j

    @property
    def lonlat(self):
        """Corners west longitude and latitude (deg)."""
        return self._cube.rlonlat[:, self.j, self.i, :]

    @property
    def limb(self):
        """Is all pixel corners are all at the limb."""
        return self._cube.rlimb[self.j, self.i]

    @property
    def ground(self):
        """Is at least one pixel corner on the ground."""
        return self._cube.rground[self.j, self.i]

    @property
    def ground_lonlat(self):
        """Corners west longitude and latitude (deg)."""
        return self.lonlat if self.ground else None

    @property
    def path(self):
        """Ground corners matplotlib path."""
        verts = np.vstack([self.lonlat.T, self.lonlat[:, 0]])
        return Path(verts, CODES['corners']) if self.ground else None

    def poly(self, **kwargs):
        """Ground corners matplotlib polygon."""
        return PathPatch(self.path, **kwargs) if self.ground else \
            PathPatch([[0, 0], [0, 0]])


class VIMSPixelFootpint(VIMSPixelCorners):
    """VIMS footprint object.

    Parameters
    ----------
    pixel: pyvims.VIMSPixel
        Parent VIMS cube pixel.

    """

    def __init__(self, pixel):
        super().__init__(pixel)

    def __str__(self):
        return f'{self._cube}-S{self.s}_L{self.l}-footprint'

    @property
    def lonlat(self):
        """Corners west longitude and latitude (deg)."""
        return self._cube.flonlat[:, self.j, self.i, :]

    @property
    def limb(self):
        """Is all pixel corners are all at the limb."""
        return self._cube.flimb[self.j, self.i]

    @property
    def ground(self):
        """Is at least one pixel corner on the ground."""
        return self._cube.fground[self.j, self.i]

    @property
    def path(self):
        """Ground corners matplotlib path."""
        return Path(self.lonlat.T, CODES['footprint']) if self.ground else None
