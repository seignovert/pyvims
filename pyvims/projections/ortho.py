"""Orthographic projection module."""

import numpy as np

from .__main__ import GroundProjection


class Orthographic(GroundProjection):
    """Orthographic projection object.

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
    https://proj.org/operations/projections/ortho.html
    https://github.com/proj4js/proj4js/blob/master/lib/projections/ortho.js

    """

    EPSILON = 1e-18

    PROJ4 = 'ortho'  # Proj4 projection key

    def __init__(self, lon_w_0=0, lat_0=0, target=None, radius=None):
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
        clat, slat = self._cs(lat)
        cdlon, sdlon = self._cs(np.subtract(self.lon_w_0, lon_w))

        g = self.slat0 * slat + self.clat0 * clat * cdlon

        if np.ndim(g) == 0 and g < self.EPSILON:
            return None, None  # Far-side

        x = self.r * clat * sdlon
        y = self.r * (self.clat0 * slat - self.slat0 * clat * cdlon)

        if np.ndim(g) > 0:
            cond = np.less(g, self.EPSILON, where=~np.isnan(g)) | np.isnan(g)
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

        if np.ndim(rh) == 0 and rh > 1:
            return None, None

        if np.ndim(rh) > 0:
            limb = rh > 1
            rh[limb] = self.r

        c = np.arcsin(rh / self.r)
        cosc, sinc = np.cos(c), np.sin(c)

        lat = np.arcsin(cosc * self.slat0 + y / rh * sinc * self.clat0)
        if self.clat0 < self.EPSILON:
            lon_w = np.arctan2(x, np.invert(y)) if self.lat_0 >= 0 else \
                -np.arctan2(np.invert(x), y)
        else:
            lon_w = np.arctan2(sinc * x, rh * self.clat0 * cosc - self.slat0 * sinc * y)

        if np.ndim(rh) > 0:
            cond = np.less_equal(rh, self.EPSILON, where=~np.isnan(rh)) | np.isnan(rh)
            lon_w[cond] = 0
            lat[cond] = np.radians(self.lat_0)
            # Remove limb data
            lon_w[limb] = np.nan
            lat[limb] = np.nan

        return (self.lon_w_0 - np.degrees(lon_w)) % 360, np.degrees(lat)
