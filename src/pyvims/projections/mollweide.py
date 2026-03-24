"""Mollweide projection module."""

import numpy as np

from .__main__ import GroundProjection


class Mollweide(GroundProjection):
    """Mollweide projection object.

    Also known as:
        * Babinet projection
        * Homalographic projection
        * Homolographic projection
        * Elliptical projection

    Parameters
    ----------
    lon_w_0: float, optional
        Center west longitude.
    target: str or pyvims.planets.Planet
        Planet name.
    radius: float, optional
        Planet radius [km]. Use the target mean radius if
        the target is a `Planet` object.

    Source
    ------
    https://proj.org/operations/projections/moll.html
    https://github.com/proj4js/proj4js/blob/master/lib/projections/moll.js

    """

    DEFAULT_RADIUS_KM = 1e-3 / np.sqrt(2)   # Unitary degree representation

    PROJ4 = 'moll'  # Proj4 projection key

    MAX_ITER = int(1e6)

    def __init__(self, lon_w_0=0, target=None, radius=None):
        self.lon_w_0 = lon_w_0
        self.target = target
        self.radius = radius

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

        self.__rx = self.__r * np.sqrt(2) / (np.pi / 2)
        self.__ry = self.__r * np.sqrt(2)

    @property
    def r(self):
        """Target planet radius [m]."""
        return self.__r

    @property
    def rx(self):
        """Auxiliary x-radius."""
        return self.__rx

    @property
    def ry(self):
        """Auxiliary y-radius."""
        return self.__ry

    @property
    def proj4(self):
        """Proj4 definition."""
        return ' '.join([
            f'+proj={self.PROJ4}',
            f'+lon_0={self.lon_0}',
            '+x_0=0',
            '+y_0=0',
            f'+R={self.r}',
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
            f'PARAMETER["central_meridian", {self.lon_0}],'
            'UNIT["Meter", 1]]'
        )

    @property
    def extent(self):
        """Image full extent."""
        return [-2 * self.ry, 2 * self.ry, -self.ry, self.ry]

    def _theta(self, lat):
        """Latitude auxiliary θ angle.

        2θ + sin 2θ = π sin lat

        Solve with Newton-Raphson iterations:

            Θⁿ⁺¹ = Θⁿ - (Θⁿ + sin Θⁿ - π sin lat) / (1 + cos Θⁿ)

        with Θ = 2θ.

        Parameters
        ----------
        lat: float or array
            Latitude [degree].

        Returns
        -------
        float or array
            Auxiliary theta angle [radians].

        Raises
        ------
        RuntimeError
            If the convergence is not reach after
            ``MAX_ITER`` iterations.

        """
        if np.ndim(lat) == 0 and abs(lat) >= 90:
            return np.pi / 2 if lat > 0 else -np.pi / 2

        # Init θ value
        theta = np.radians(lat).ravel()

        # |Lat| >= 90 - Remove poles
        cond = np.abs(theta) >= np.pi / 2
        theta[cond] = np.pi / 2 * np.sign(theta[cond])

        # |Lat| < 90 - Create dynamical array
        np.logical_not(cond, out=cond)
        _theta = theta[cond]
        _itheta = np.arange(np.prod(theta.shape), dtype=np.uint32)[cond]
        _theta_0 = np.pi * np.sin(_theta)

        # Newton-Raphson iterate on dynamical array
        for _ in range(self.MAX_ITER):
            if not len(_theta):
                break

            # sin Θⁿ + Θⁿ - π sin lat
            _stheta = np.sin(_theta)
            np.add(_stheta, _theta, out=_stheta)
            np.subtract(_stheta, _theta_0, out=_stheta)

            # 1 + cos Θⁿ
            _ctheta = np.cos(_theta)
            np.add(1, _ctheta, out=_ctheta)

            # Θⁿ - (Θⁿ + sin Θⁿ - π sin lat) / (1 + cos Θⁿ)
            np.divide(_stheta, _ctheta, out=_stheta)
            np.subtract(_theta, _stheta, out=_theta)

            # Convergence reached
            cond = np.abs(_stheta) <= self.EPSILON
            np.divide(_theta[cond], 2, out=theta[_itheta[cond]])

            # Keep only the points not converged
            np.logical_not(cond, out=cond)
            _theta = _theta[cond]
            _theta_0 = _theta_0[cond]
            _itheta = _itheta[cond]

        else:
            raise RuntimeError('Convergence not reach on θ.')

        return theta[0] if np.ndim(lat) == 0 else theta.reshape(np.shape(lat))

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
        if np.ndim(lat) == 0 and np.abs(lat) >= 90:
            return 0, self.ry if lat > 0 else -self.ry

        dlon = np.radians((np.subtract(self.lon_w_0, lon_w) + 180) % 360 - 180)

        if np.ndim(lon_w) == 0 and self.lon_w_0 - lon_w == 180:
            dlon *= -1
        elif np.ndim(lon_w) > 0:
            dlon[np.subtract(self.lon_w_0, lon_w) == 180] *= -1

        theta = self._theta(lat)
        x = self.rx * dlon * np.cos(theta)
        y = self.ry * np.sin(theta)

        # x is auto-broadcast on `lat` shape through `theta`
        if np.ndim(x) > 0 and np.ndim(y) == 0:
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
        if np.ndim(y) == 0 and abs(y / self.ry) > 1:
            return (None, None)
        elif np.ndim(y) > 0:
            theta = np.divide(y, self.ry)
            np.clip(theta, -1, 1, out=theta)
            np.arcsin(theta, out=theta)
        else:
            theta = np.arcsin(y / self.ry)

        lon_w = np.divide(x, self.rx * np.cos(theta))

        if np.ndim(lon_w) == 0 and abs(lon_w) > np.pi:
            return (None, None)

        lat = np.degrees(np.arcsin((2 * theta + np.sin(2 * theta)) / np.pi))

        # lon is auto-broadcast on `y` shape through `theta`
        if np.ndim(lon_w) > 0 and np.ndim(lat) == 0:
            lat = np.copy(np.broadcast_to(lat, lon_w.shape))

        if np.ndim(lon_w) > 0:
            cond = (np.abs(lon_w) > np.pi) | (np.abs(y / self.ry) > 1)
            lon_w[cond] = np.nan
            lat[cond] = np.nan

        lon_w = (self.lon_w_0 - np.degrees(lon_w)) % 360

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

        """
        raise NotImplementedError
