"""Abstract projection module."""

import numpy as np

from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

from ..planets import PLANETS


class Projection:
    """Abstract ground projection object."""

    EPSILON = 1e-10

    def __str__(self):
        return self.__class__.__name__

    def __call__(self, *args, invert=False):
        """Project geographic point in X-Y coordinates (or reverse)."""
        if len(args) == 1:
            if isinstance(args[0], PatchCollection):
                return self.xy_collection(args[0])

            if isinstance(args[0], PathPatch):
                return self.xy_patch(args[0])

            if isinstance(args[0], Path):
                return self.xy_path(args[0])

        if len(args) == 2 or (len(args) == 3 and self.PROJ4 == 'ortho'):
            return self.lonlat(*args) if invert else self.xy(*args)

        raise ValueError('A `PatchCollection`, `PathPatch`, `Patch` '
                         'or (lon_w, lat) attributes are required.')

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

    def _vc(self, path):
        """Get projected vertices and codes (and close the polygon if needed).

        Parameters
        ----------
        path: matplotlib.path.Path
            Matplotlib path in west-longitude and latitude coordinates.

        Returns
        -------
        [float], [float], [int]
            X and Y vertices and path code.

        """
        x, y = self.xy(*path.vertices.T)

        # Add codes if missing
        if path.codes is None:
            codes = [Path.MOVETO] + [Path.LINETO] * (len(x) - 2) + [Path.CLOSEPOLY]
        else:
            codes = path.codes

        # Close the path
        if x[0] != x[-1] or y[0] != y[-1]:
            x = np.concatenate([x, [x[0]]])
            y = np.concatenate([y, [y[0]]])

            if codes[-1] == Path.CLOSEPOLY:
                codes = np.concatenate([codes[:-1], [Path.LINETO, Path.CLOSEPOLY]])
            else:
                codes = np.concatenate([codes, [Path.CLOSEPOLY]])

        return np.transpose([x, y]), codes

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
        return None if path is None else Path(*self._vc(path))

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

    def meridians(self, lons=None, exclude=None,
                  lon_min=0, lon_max=359, dlon=30,
                  lat_min=-80, lat_max=80, nlat=50):
        """Projected meridians grid."""
        if lons is None:
            lons = np.arange(lon_min, lon_max, dlon)
        elif isinstance(lons, (int, float)):
            lons = [lons]

        if exclude is None or isinstance(exclude, (int, float)):
            exclude = [] if exclude is None else [exclude]

        return np.moveaxis([
            self(lon, np.linspace(lat_min, lat_max, nlat)) for lon in lons
            if lon not in exclude
        ], 0, 2)

    def parallels(self, lats=None, exclude=None,
                  lat_min=-80, lat_max=80, dlat=10,
                  lon_min=0, lon_max=360, nlon=50):
        """Orthographic parallels grid."""
        if lats is None:
            lats = np.arange(lat_min, lat_max + dlat, dlat)
        elif isinstance(lats, (int, float)):
            lats = [lats]

        if exclude is None or isinstance(exclude, (int, float)):
            exclude = [] if exclude is None else [exclude]

        return np.moveaxis([
            self(np.linspace(lon_min, lon_max, nlon), lat) for lat in lats
            if lat not in exclude
        ], 0, 2)


class GroundProjection(Projection):
    """Abstract ground projection object.

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

    DEFAULT_RADIUS_KM = 1e-3  # = 1 [m]

    PROJ4 = None  # Proj4 projection key

    def __init__(self, lon_w_0=0, lat_0=0, target=None, radius=None):
        self.lon_w_0 = lon_w_0
        self.lat_0 = lat_0
        self.target = target
        self.radius = radius

    def __repr__(self):
        return (f'<{self}> Target: {self.target}'
                f'\n\tProj4: `{self.proj4}`')

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
    def target(self):
        """Planet target."""
        return self.__target

    @target.setter
    def target(self, name):
        """Set target name."""
        self.__target = 'Undefined' if name is None \
            else name if name not in PLANETS else PLANETS[name]

    @property
    def radius(self):
        """Target planet radius [km]."""
        return self.__r * 1e-3

    @radius.setter
    def radius(self, value_km):
        """Set radius and convert from [km] to [m]."""
        if isinstance(self.target, str):
            if value_km is None:
                self.__r = self.DEFAULT_RADIUS_KM * 1e3
            else:
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
            f'SPHEROID["{self.target}_Mean_Sphere", {int(self.r)}, 0]],'
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
