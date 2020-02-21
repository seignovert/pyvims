"""VIMS pixel corners module."""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

from .img import rgb
from .misc.vertices import area
from .projections.lambert import xy as lambert
from .projections import Path3D


class VIMSPixelCorners:
    """VIMS corners object.

    Parameters
    ----------
    pixel: pyvims.VIMSPixel
        Parent VIMS cube pixel.

    """

    CODES = [Path.MOVETO] + [Path.LINETO] * 3 + [Path.CLOSEPOLY]

    def __init__(self, pixel):
        self._pix = pixel
        self.__lpath = None

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
    def alt(self):
        """Corners altitude (km)."""
        return self._cube.ralt[self.j, self.i, :]

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
    def vertices(self):
        """Corners vertices."""
        return np.vstack([self.lonlat.T, self.lonlat[:, 0]])

    def _lambert(self, lonlat):
        """Lambert azimuthal equal-area projection in mean sub-spacecraft plane."""
        return lambert(*lonlat, *self._cube.sc)

    @property
    def _lambert_path(self):
        """Lambert projected ground corners matplotlib path."""
        if self.__lpath is None and self.ground:
            self.__lpath = Path(self._lambert(self.vertices.T).T, self.CODES)
        return self.__lpath

    def contains(self, pts):
        """Check if points are inside the pixel.

        Parameters
        ----------
        pts: np.array
            List of geographic point(s): ``(lon_w, lat)`` or ``[(lon_w, lat), …]``

        Returns
        -------
        np.array
            Return ``TRUE`` if the point is inside the pixel corners, and
            ``FALSE`` overwise.

        Note
        ----
        The points location are first projected on the sub-spacecraft
        mean plane with a Lambert azimuthal equal-area projection to avoid
        polar and meridian crossing error on polygon paths.

        By default, if the pixel is fully at the limb (no corners touching
        the ground), the intersection is not calculated and return a global
        ``FALSE`` value.

        """
        if self.limb:
            return False

        if np.ndim(pts) == 1:
            pts = [pts]

        _lambert_pts = self._lambert(np.transpose(pts)).T
        return self._lambert_path.contains_points(_lambert_pts)

    def __contains__(self, item):
        """Check the item is inside the pixel."""
        if np.size(item) != 2 or np.ndim(item) == 0:
            raise ValueError('Coordinate point must be a 2 dimension array: '
                             '`(west_longitude, latitude)`')

        if np.ndim(item) != 1:
            raise ValueError('Only a single point can be tested. '
                             'Use `.contains()` function for multiple points.')

        return self.contains([item])

    @property
    def is_npole(self):
        """Check if the North Pole is inside the pixel."""
        return (0, 90) in self

    @property
    def is_spole(self):
        """Check if the South Pole is inside the pixel."""
        return (0, -90) in self

    @property
    def path(self):
        """Ground corners matplotlib path."""
        return Path(self.vertices, self.CODES) if self.ground else None

    @property
    def path3d(self):
        """Ground corners matplotlib path."""
        return Path3D(self.vertices, codes=self.CODES, alt=[*self.alt, self.alt[0]])

    def patch(self, alt=False, **kwargs):
        """Ground corners matplotlib patch."""
        return PathPatch(self.path3d if alt else self.path, **kwargs)

    @property
    def area(self):
        """Corners area on the ground.

        Use lambert equal-area projected pixel
        centered on the mean sub-spacecraft point.

        """
        return area(self._lambert_path.vertices) * self._cube.target_radius ** 2


class VIMSPixelFootprint(VIMSPixelCorners):
    """VIMS footprint object.

    Parameters
    ----------
    pixel: pyvims.VIMSPixel
        Parent VIMS cube pixel.

    """

    CODES = [Path.MOVETO] + [Path.LINETO] * 7 + [Path.CLOSEPOLY]

    def __init__(self, pixel):
        super().__init__(pixel)

    def __str__(self):
        return f'{self._cube}-S{self.s}_L{self.l}-footprint'

    @property
    def lonlat(self):
        """Corners west longitude and latitude (deg)."""
        return self._cube.flonlat[:, self.j, self.i, :]

    @property
    def alt(self):
        """Corners altitude (km)."""
        return self._cube.falt[self.j, self.i, :]

    @property
    def limb(self):
        """Is all pixel corners are all at the limb."""
        return self._cube.flimb[self.j, self.i]

    @property
    def ground(self):
        """Is at least one pixel corner on the ground."""
        return self._cube.fground[self.j, self.i]

    @property
    def vertices(self):
        """Footprint vertices."""
        return self.lonlat.T

    @property
    def path3d(self):
        """Ground corners matplotlib path."""
        return Path3D(self.vertices, codes=self.CODES, alt=self.alt)


class VIMSPixelsCorners:
    """VIMS pixels corners collection.

    Parameters
    ----------
    pixels: pyvims.VIMSPixels
        Parent VIMS cube pixels.

    """

    def __init__(self, pixels):
        self._pixels = pixels
        self.corners = [pix.corners for pix in pixels]
        self.__paths = None
        self.__paths3d = None

    def __str__(self):
        return f'{self._pixels}-Corners'

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> {self}',
            f'Vertices shape: {self.vertices.shape}'
        ])

    def __len__(self):
        return len(self.corners)

    def __iter__(self):
        return iter(self.corners)

    @property
    def vertices(self):
        """Corners vertices."""
        return np.array([c.vertices for c in self])

    @property
    def ground(self):
        """Check if at least one corner is on the ground."""
        return np.array([c.ground for c in self])

    @property
    def paths(self):
        """List of corners paths."""
        if self.__paths is None:
            self.__paths = np.ma.array([c.path for c in self],
                                       mask=~self.ground,
                                       fill_value=None)
        return self.__paths

    @property
    def paths3d(self):
        """List of corners paths 3D (with altitude)."""
        if self.__paths3d is None:
            self.__paths3d = [c.path3d for c in self]
        return self.__paths3d

    def collection(self, index='surface', facecolors=None, edgecolors='None',
                   vmin=None, vmax=None, cmap=None, alt=False, **kwargs):
        """Get the collection of all the corners patches on the ground."""
        patches = [PathPatch(path) for path in (self.paths3d if alt else self.paths.data)]

        if not isinstance(facecolors, str):
            if facecolors is None:
                data = self._pixels._cube[index]  # pylint: disable=protected-access
            else:
                data = facecolors

            if cmap is None:
                if np.ndim(data) == 2:
                    data = rgb(data, data, data, imin=vmin, imax=vmax)

                facecolors = np.reshape(data, (self._pixels.NP, 3)) / 255
            else:
                if vmin is None:
                    vmin = np.nanmin(data)

                if vmax is None:
                    vmax = np.nanmax(data)

                data = np.clip((data - vmin) / (vmax - vmin), 0, 1)
                data = plt.cm.get_cmap(cmap)(data)

                facecolors = np.reshape(data, (self._pixels.NP, 4))

        return PatchCollection(patches,
                               edgecolors=edgecolors,
                               facecolors=facecolors,
                               cmap=cmap,
                               **kwargs)


class VIMSPixelsFootprint(VIMSPixelsCorners):
    """VIMS pixels footprint collection.

    Parameters
    ----------
    pixels: pyvims.VIMSPixels
        Parent VIMS cube pixels.

    """

    def __init__(self, pixels):
        super().__init__(pixels)
        self.corners = [pix.footprint for pix in self._pixels]

    def __str__(self):
        return f'{self._pixels}-Footprint'
