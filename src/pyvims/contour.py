"""VIMS cube contour module."""

import numpy as np

from matplotlib.patches import PathPatch
from matplotlib.path import Path

from .projections.lambert import xy as lambert
from .vertices import path_cross_180, path_cross_360, path_pole_180, path_pole_360
from .vectors import deg180, deg360


class VIMSContour:
    """VIMS FOV contour object.

    Parameters
    ----------
    cube: pyvims.VIMS
        Parent VIMS cube.

    """
    CODES = None

    def __init__(self, cube):
        self._cube = cube
        self.__lpath = None

    def __str__(self):
        return f'{self._cube}-contour'

    def __repr__(self):
        return f'<{self.__class__.__name__}> {self}'

    def __len__(self):
        return self.vertices.shape[0]

    def __call__(self, **kwargs):
        return self.patch(**kwargs)

    def __iter__(self):
        return iter(self.path.vertices.T)

    @property
    def lonlat(self):
        """Contour west longitude and latitude (deg)."""
        return self._cube.clonlat

    @property
    def alt(self):
        """Is all pixel contour are all at the limb."""
        return self._cube.calt

    @property
    def vertices(self):
        """Contour vertices."""
        return np.vstack([self.lonlat.T, self.lonlat[:, 0]])

    @property
    def vertices_e(self):
        """Contour vertices in east longitude."""
        lon_w, lat = self.vertices.T
        lon_e = deg180(-lon_w)
        return np.vstack([lon_e, lat]).T

    @property
    def _codes(self):
        return [Path.MOVETO] + [Path.LINETO] * (len(self) - 2) + [Path.CLOSEPOLY]

    def _lambert(self, lonlat):
        """Lambert azimuthal equal-area projection in mean sub-spacecraft plane."""
        return lambert(*lonlat, *self._cube.sc)

    @property
    def _lambert_path(self):
        """Lambert projected contour matplotlib path."""
        if self.__lpath is None:
            self.__lpath = Path(self._lambert(self.vertices.T).T, self._codes)
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
            Return ``TRUE`` if the point is inside the pixel contour, and
            ``FALSE`` overwise.

        Note
        ----
        The points location are first projected on the sub-spacecraft
        mean plane with a Lambert azimuthal equal-area projection to avoid
        polar and meridian crossing error on polygon paths.

        """
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
        """Ground contour polygon in ]-180°, 180°] equirectangular projection."""
        return PathPatch(self.path_180, **kwargs)

    def patch_360(self, **kwargs):
        """Ground contour polygon in [0°, 360°[ equirectangular projection."""
        return PathPatch(self.path_360, **kwargs)

    @property
    def path(self):
        """Ground contour path."""
        return self.path_360

    def patch(self, **kwargs):
        """Ground contour polygon patch."""
        return self.patch_360(**kwargs)
