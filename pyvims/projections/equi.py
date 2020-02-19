"""Equirectangular projection module."""

import numpy as np

from matplotlib.path import Path

from .__main__ import GroundProjection


class Equirectangular(GroundProjection):
    """Equirectangular projection object.

    a.k.a. `Plate Carrée` and `Equidistant Cylindrical`.

    Parameters
    ----------
    lon_w_0: float, optional
        Center west longitude.
    lat_0: float, optional
        Center latitude (North Pole by default).
    lat_ts: float, optional
        Latitude of true scale.
    target: str or pyvims.planets.Planet
        Planet name.
    radius: float, optional
        Planet radius [km]. Use the target mean radius if
        the target is a `Planet` object.

    Source
    ------
    https://proj.org/operations/projections/eqc.html
    https://github.com/proj4js/proj4js/blob/master/lib/projections/eqc.js

    """

    DEFAULT_RADIUS_KM = 180e-3 / np.pi   # Unitary degree representation

    PROJ4 = 'eqc'  # Proj4 projection key

    def __init__(self, lon_w_0=180, lat_0=0, lat_ts=0, target=None, radius=None):
        self.lon_w_0 = lon_w_0
        self.lat_0 = lat_0
        self.target = target
        self.radius = radius
        self.lat_ts = lat_ts

    @property
    def lat_ts(self):
        """Latitude of true scale [degree]."""
        return self.__lat_ts

    @lat_ts.setter
    def lat_ts(self, value):
        """Set latitude of true scale value."""
        self.__lat_ts = value
        self.__rc = np.cos(np.radians(value))
        self.__xc = np.pi * self.r * self.__rc
        self.__yc = np.pi / 2 * self.r

    @property
    def rc(self):
        """Cosine of latitude of origin."""
        return self.__rc

    @property
    def xc(self):
        """Projected x crossing meridian value."""
        return self.__xc

    @property
    def yc(self):
        """Projected y pole value."""
        return self.__yc

    @property
    def proj4(self):
        """Proj4 definition."""
        return ' '.join([
            f'+proj={self.PROJ4}',
            f'+lat_0={self.lat_0}',
            f'+lon_0={self.lon_0}',
            f'+lat_ts={self.lat_ts}',
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
            f'PARAMETER["standard_parallel_1", {self.lat_ts}],'
            f'PARAMETER["central_meridian", {self.lon_0}],'
            f'PARAMETER["latitude_of_origin", {self.lat_0}],'
            'UNIT["Meter", 1]]'
        )

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
        dlon = np.radians((np.subtract(self.lon_w_0, lon_w) + 180) % 360 - 180)
        dlat = np.radians(np.subtract(lat, self.lat_0))

        if np.ndim(lon_w) == 0 and (self.lon_w_0 - lon_w) == 180:
            dlon = np.pi
        elif np.ndim(lon_w) > 0:
            dlon[np.equal(lon_w, self.lon_w_0 - 180)] = np.pi

        x = self.r * dlon * self.rc
        y = self.r * dlat

        if np.ndim(x) == 0 and np.ndim(y) > 0:
            x = np.broadcast_to(x, y.shape)
        elif np.ndim(x) > 0 and np.ndim(y) == 0:
            y = np.broadcast_to(y, x.shape)

        return x, y

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
        lon_w = (-np.degrees(np.divide(x, self.r * self.rc)) - self.lon_w_0) % 360
        lat = np.degrees(np.divide(y, self.r)) + self.lat_0

        if np.ndim(x) == 0 and np.abs(lon_w - 360) < 1e-5:
            lon_w = 0
        elif np.ndim(x) > 0:
            lon_w[np.abs(lon_w - 360) < 1e-5] = 0

        if np.ndim(lon_w) == 0 and np.ndim(lat) > 0:
            lon_w = np.broadcast_to(lon_w, lat.shape)
        elif np.ndim(lon_w) > 0 and np.ndim(y) == 0:
            lat = np.broadcast_to(lat, lon_w.shape)

        return lon_w, lat

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

        Raises
        ------
        ValueError
            If the polygon cross more than 2 times the anti-meridian.

        """
        if path is None:
            return None

        vertices, codes = self._vc(path)

        x, y = vertices.T
        cross = np.abs(x[1:] - x[:-1]) > self.xc  # [i + 1] - [i]
        n_cross = np.sum(cross)

        if n_cross == 1:
            vertices, codes = self._cross_pole(x, y, cross)
        elif n_cross == 2:
            vertices, codes = self._cross_antimeridian(x, y)
        elif n_cross > 2:
            raise ValueError('Path vertices cross more than 2 time the anti-meridian.')

        return Path(vertices, codes)

    def _cross_pole(self, x, y, cross):
        """Redraw vertices path around the North/South Pole.

        Parameters
        ----------
        x: [float]
            Map x coordinate.
        y: [float]
            Map y coordinate.
        cross: [bool]
            Bool list if the vertices crossed the anti-meridian.

        Returns
        -------
        matplotlib.path.Path
            New vertice surrounding the pole.

        """
        pole = self.yc if y[np.argmax(np.abs(y))] >= 0 else -self.yc

        verts = [[x[0], y[0]]]
        for i in range(len(cross)):
            if cross[i]:
                if x[i] > 0:
                    _x1, _x2 = self.xc, -self.xc  # Right cross
                    _f = (self.xc - x[i]) / (x[i + 1] + 2 * self.xc - x[i])
                else:
                    _x1, _x2 = -self.xc, self.xc  # Left cross
                    _f = (self.xc + x[i]) / (x[i] - x[i + 1] + 2 * self.xc)

                _y = (y[i + 1] - y[i]) * _f + y[i]

                verts.append([_x1, _y])
                verts.append([_x1, pole])
                verts.append([_x2, pole])
                verts.append([_x2, _y])

            verts.append([x[i + 1], y[i + 1]])

        codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) + [Path.CLOSEPOLY]

        return verts, codes

    def _cross_antimeridian(self, x, y):
        """Redraw vertices path around the anti-meridian.

        Parameters
        ----------
        x: [float]
            Map x coordinate.
        y: [float]
            Map y coordinate.

        Returns
        -------
        matplotlib.path.Path
            New vertice (in 2 pieces) splitted by the anti-meridian.

        """
        npt = len(x) - 1

        # Right polygon
        rv = []
        _xr = x % (2 * self.xc)
        for i in range(npt):
            if _xr[i] <= self.xc:
                rv.append([_xr[i], y[i]])

            if (_xr[i] <= self.xc and _xr[i + 1] > self.xc) \
                    or (_xr[i] > self.xc and _xr[i + 1] <= self.xc):

                _f = (self.xc - _xr[i]) / (_xr[i + 1] - _xr[i])
                _y = (y[i + 1] - y[i]) * _f + y[i]
                rv.append([self.xc, _y])

        rv.append(rv[0])

        # Left polygon
        lv = []
        _xl = _xr - 2 * self.xc
        for i in range(npt):
            if _xl[i] >= -self.xc:
                lv.append([_xl[i], y[i]])

            if (_xl[i] >= -self.xc and _xl[i + 1] < -self.xc) \
                    or (_xl[i] < -self.xc and _xl[i + 1] >= -self.xc):

                _f = (-self.xc - _xl[i]) / (_xl[i + 1] - _xl[i])
                _y = (y[i + 1] - y[i]) * _f + y[i]
                lv.append([-self.xc, _y])

        lv.append(lv[0])

        # Create codes
        codes = ([Path.MOVETO] + [Path.LINETO] * (len(lv) - 2) + [Path.CLOSEPOLY]
                 + [Path.MOVETO] + [Path.LINETO] * (len(rv) - 2) + [Path.CLOSEPOLY])

        return np.vstack([lv, rv]), codes
