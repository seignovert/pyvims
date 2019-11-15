"""VIMS pixel corners module."""

import numpy as np

from matplotlib.patches import PathPatch
from matplotlib.path import Path

from .projections.lambert import xy as lambert
from .vertices import area, path_cross_180, path_cross_360, path_pole_180, path_pole_360
from .vectors import deg180, deg360


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

    @property
    def vertices_e(self):
        """Corners vertices in east longitude."""
        lon_w, lat = self.vertices.T
        lon_e = deg180(-lon_w)
        return np.vstack([lon_e, lat]).T

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
    def is_180(self):
        """Check if the pixel cross the change of date meridian (180°)."""
        lon_e = deg180(-self.lonlat[0])
        return lon_e.max() - lon_e.min() > 180

    @property
    def is_360(self):
        """Check if the pixel cross the prime meridian (360°)."""
        lon_w = deg360(self.lonlat[0])
        return lon_w.max() - lon_w.min() > 180

    @property
    def path_180(self):
        """Polygon path in ]-180°, 180°] equirectangular projection."""
        if self.limb:
            return None

        if self.is_npole:
            verts, codes = path_pole_180(self.vertices_e, npole=True)

        elif self.is_spole:
            verts, codes = path_pole_180(self.vertices_e, npole=False)

        elif self.is_180:
            verts, codes = path_cross_180(self.vertices_e)

        else:
            verts, codes = self.vertices_e, self.CODES

        return Path(verts, codes)

    @property
    def path_360(self):
        """Polygon path in [0°, 360°[ equirectangular projection."""
        if self.limb:
            return None

        if self.is_npole:
            verts, codes = path_pole_360(self.vertices, npole=True)

        elif self.is_spole:
            verts, codes = path_pole_360(self.vertices, npole=False)

        elif self.is_360:
            verts, codes = path_cross_360(self.vertices)

        else:
            verts, codes = self.vertices, self.CODES

        return Path(verts, codes)

    def patch_180(self, **kwargs):
        """Ground corners matplotlib patch in ]-180°, 180°] equirectangular projection."""
        return PathPatch(self.path_180, **kwargs) if self.ground else \
            PathPatch([[0, 0], [0, 0]])

    def patch_360(self, **kwargs):
        """Ground corners matplotlib patch in [0°, 360°[ equirectangular projection."""
        return PathPatch(self.path_360, **kwargs) if self.ground else \
            PathPatch([[0, 0], [0, 0]])

    @property
    def path(self):
        """Ground corners matplotlib path."""
        return self.path_360

    def patch(self, **kwargs):
        """Ground corners matplotlib patch."""
        return self.patch_360(**kwargs)

    @property
    def area(self):
        """Corners area on the ground.

        Use lambert equal-area projected pixel
        centered on the mean sub-spacecraft point.

        """
        return area(self._lambert_path.vertices) * self._cube.target_radius ** 2


class VIMSPixelFootpint(VIMSPixelCorners):
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
