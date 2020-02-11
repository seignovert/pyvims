"""Abstract projection module."""

import numpy as np

from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection


class Projection:
    """Abstract projection object.

    Parameters
    ----------
    lon_w_0: float, optional
        Center west longitude.
    lat_0: float, optional
        Center latitude.
    target: str or pyvims.planets.Planet
        Planet name.
    radius: float, optional
        Planet radius [km]. Use the target mean radius if
        the target is a `Planet` object.

    """

    EPSILON = 1e-10

    PROJ4 = None  # Proj4 projection key

    def __init__(self, lon_w_0=0, lat_0=0, target=None, radius=1):
        self.lon_w_0 = lon_w_0
        self.lat_0 = lat_0
        self.target = target
        self.radius = radius

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return f'<{self}> {self.target}\n\tProj4: `{self.proj4}`'

    def __call__(self, *args, invert=False):
        """Project geographic point in X-Y coordinates (or reverse)."""
        if len(args) == 1:
            if isinstance(args[0], PatchCollection):
                return self.xy_collection(args[0])

            if isinstance(args[0], PathPatch):
                return self.xy_patch(args[0])

            if isinstance(args[0], Path):
                return self.xy_path(args[0])

        if len(args) == 2:
            return self.lonlat(args[0], args[1]) if invert else self.xy(args[0], args[1])

        raise ValueError('A `PatchCollection`, `PathPatch`, `Patch` '
                         'or (lon_w, lat) attributes are required.')

    @property
    def lat_0(self):
        """Latitude of origin [degree]."""
        return self.__lat_0

    @lat_0.setter
    def lat_0(self, value):
        """Set latitude of origin value."""
        self.__lat_0 = value
        self.__clat0, self.__slat0 = self._cs(value)

    @property
    def clat0(self):
        """Cosine of latitude of origin."""
        return self.__clat0

    @property
    def slat0(self):
        """Sine of latitude of origin."""
        return self.__slat0

    @property
    def lon_w_0(self):
        """West central meridian [degree]."""
        return self.__lon_w_0

    @lon_w_0.setter
    def lon_w_0(self, value):
        """Set west central meridian value."""
        self.__lon_w_0 = value
        self.__clon0, self.__slon0 = self._cs(value)

    @property
    def lon_0(self):
        """East central meridian [degree]."""
        return ((-self.lon_w_0 + 180) % 360 - 180) if np.abs(self.lon_w_0) != 180 else 180

    @property
    def clon0(self):
        """Cosine of west central meridian."""
        return self.__clon0

    @property
    def slon0(self):
        """Sine of west central meridian."""
        return self.__slon0

    @property
    def radius(self):
        """Target planet radius [km]."""
        return self.__r * 1e-3

    @radius.setter
    def radius(self, value_km):
        """Set radius and convert from [km] to [m]."""
        if self.target is None or isinstance(self.target, str):
            self.__r = value_km * 1e3
        else:
            self.__r = self.target.radius * 1e3

    @property
    def r(self):
        """Target planet radius [m]."""
        return self.__r

    @property
    def proj4(self):
        """Proj4 definition."""
        return ' '.join([
            f'+proj={self.PROJ4}',
            f'+lat_0={self.lat_0}',
            f'+lon_0={self.lon_0}',
            '+k=1',
            '+x_0=0',
            '+y_0=0',
            f'+a={self.r}',
            f'+b={self.r}',
            '+units=m',
            '+no_defs',
        ])

    @property
    def wkt(self):
        """WKT definition."""
        return (
            f'PROJCS["PROJCS_{self.target}_{self}",'
            f'GEOGCS["GCS_{self.target}",'
            f'DATUM["D_{self.target}",'
            f'SPHEROID["{self.target}_MEAN_SPHERE", {int(self.r)}, 0]],'
            'PRIMEM["Greenwich",0],'
            'UNIT["Degree",0.017453292519943295]],'
            f'PROJECTION["{self}"],'
            'PARAMETER["false_easting", 0],'
            'PARAMETER["false_northing", 0],'
            'PARAMETER["scale_factor", 1],'
            f'PARAMETER["central_meridian", {self.lon_0}],'
            f'PARAMETER["latitude_of_origin", {self.lat_0}],'
            'UNIT["Meter", 1]]'
        )

    @staticmethod
    def _cs(angle):
        """Cosines and sinus value of an angle [degree]."""
        theta = np.radians(angle)
        return np.cos(theta), np.sin(theta)

    def xy(self, lon_w, lat):
        """Convert latitude/longitude coordinates in map coordinates.

        Parameters
        ----------
        lon_w: float or array
            West longitude [degree].
        lat: float or array
            Latitude [degree].

        Returns
        -------
        float or array, float or array
            X-Y map coordinates.

        """
        raise NotImplementedError

    def lonlat(self, x, y):
        """Convert map coordinates in latitude/longitude coordinates.

        Parameters
        ----------
        x: float or array
            X-coordinate on the map [m].
        y: float or array
            Y-coordinate on the map [m].

        Returns
        -------
        float or array, float or array
            West longitude and latitude [degree].

        """
        raise NotImplementedError

    def xy_path(self, path):
        """Convert path vertices in map coordinates.

        Parameters
        ----------
        path: matplotlib.path.Path
            Matplotlib path in west-longitude and latitude coordinates.

        Returns
        -------
        matplotlib.path.Path
            Path in map coordinates.

        """
        if path is None:
            return None

        vertices = np.transpose(self.xy(*path.vertices.T))
        return Path(vertices, path.codes)

    def xy_patch(self, patch):
        """Convert patch vertices in map coordinates.

        Parameters
        ----------
        patch: matplotlib.patches.Patch
            Matplotlib patch in west-longitude and latitude coordinates.

        Returns
        -------
        matplotlib.patches.Patch
            Patch in map coordinates.

        Note
        ----
        Only face and edge colors are preserved.

        """
        return PathPatch(
            self.xy_path(patch.get_path()),
            facecolor=patch.get_fc(),
            edgecolor=patch.get_ec(),
        )

    def xy_collection(self, collection):
        """Convert collection vertices in map coordinates.

        Parameters
        ----------
        collection: matplotlib.collections.PatchCollection
            Matplotlib collection in west-longitude and latitude coordinates.

        Returns
        -------
        matplotlib.collections.PatchCollection
            collection in map coordinates.

        Note
        ----
        Only face and edge colors are preserved.

        """
        return PatchCollection(
            [PathPatch(self.xy_path(path)) for path in collection.get_paths()],
            facecolors=collection.get_facecolors(),
            edgecolors=collection.get_edgecolors(),
        )
