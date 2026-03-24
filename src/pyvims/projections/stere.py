"""Stereographic projection module."""

import numpy as np

from .__main__ import GroundProjection


class Stereographic(GroundProjection):
    """Stereographic projection object.

    Parameters
    ----------
    lon_w_0: float, optional
        Center west longitude.
    lat_0: float, optional
        Center latitude (North Pole by default).
    target: str or pyvims.planets.Planet
        Planet name.
    radius: float, optional
        Planet radius [km]. Use the target mean radius if
        the target is a `Planet` object.

    Source
    ------
    https://proj.org/operations/projections/stere.html
    https://github.com/proj4js/proj4js/blob/master/lib/projections/stere.js

    """

    PROJ4 = 'stere'  # Proj4 projection key

    def __init__(self, lon_w_0=0, lat_0=90, target=None, radius=None):
        self.lon_w_0 = lon_w_0
        self.lat_0 = lat_0
        self.target = target
        self.radius = radius

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
        if np.ndim(lat) == 0 and np.ndim(lon_w) == 0 \
                and np.abs(lat + self.lat_0) <= self.EPSILON:
            return None, None  # Anti-origin point

        clat, slat = self._cs(lat)
        cdlon, sdlon = self._cs(np.subtract(self.lon_w_0, lon_w))

        r = 2 * self.r / (1 + self.slat0 * slat + self.clat0 * clat * cdlon)
        x = r * clat * sdlon
        y = r * (self.clat0 * slat - self.slat0 * clat * cdlon)

        if np.ndim(lat) > 0 or np.ndim(lon_w) > 0:
            cond = np.abs(np.add(lat, self.lat_0)) <= self.EPSILON
            x[cond] = None
            y[cond] = None

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
        rh = np.sqrt(np.power(x, 2) + np.power(y, 2))
        if np.ndim(rh) == 0 and rh <= self.EPSILON:
            return self.lon_w_0, self.lat_0

        c = 2 * np.arctan(rh / (2 * self.r))
        cosc, sinc = np.cos(c), np.sin(c)

        lat = np.arcsin(cosc * self.slat0 + y / rh * sinc * self.clat0)
        if self.clat0 < self.EPSILON:
            lon_w = np.arctan2(x, np.multiply(-1, y) if self.lat_0 > 0 else y)
        else:
            lon_w = np.arctan2(sinc * x, rh * self.clat0 * cosc - self.slat0 * sinc * y)

        if np.ndim(rh) > 0:
            cond = np.less_equal(rh, self.EPSILON, where=~np.isnan(rh)) | np.isnan(rh)
            lon_w[cond] = 0
            lat[cond] = np.radians(self.lat_0)

        return (self.lon_w_0 - np.degrees(lon_w)) % 360, np.degrees(lat)
