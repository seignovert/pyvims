"""Orthographic projection module."""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.path import Path

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

    @property
    def extent(self):
        """Image full extent."""
        return [-self.r, self.r, -self.r, self.r]

    def xy(self, lon_w, lat, alt=None):
        """Convert latitude/longitude coordinates in map coordinates.

        Parameters
        ----------
        lon_w: float or array
            West longitude [degree].
        lat: float or array
            Latitude [degree].
        alt: float or array, optional
            Point altitude in [km].

        Returns
        -------
        float or array, float or array
            X-Y map coordinates.

        """
        clat, slat = self._cs(lat)
        cdlon, sdlon = self._cs(np.subtract(self.lon_w_0, lon_w))

        g = self.slat0 * slat + self.clat0 * clat * cdlon

        if np.ndim(g) == 0 and g < 0:
            return None, None  # Far-side

        x = self.r * clat * sdlon
        y = self.r * (self.clat0 * slat - self.slat0 * clat * cdlon)

        if np.ndim(g) > 0:
            cond = np.less(g, 0, where=~np.isnan(g)) | np.isnan(g)
            x[cond] = None
            y[cond] = None

        if alt is not None:
            r = 1 + np.divide(alt, self.radius)
            x = np.multiply(x, r)
            y = np.multiply(y, r)

        return x, y

    def lonlat(self, x, y, alt=False):
        """Convert map coordinates in latitude/longitude coordinates.

        Parameters
        ----------
        x: float or array
            X-coordinate on the map [m].
        y: float or array
            Y-coordinate on the map [m].
        alt: bool, optional
            Retrieve point altitude in [km].

        Returns
        -------
        float or array, float or array
            West longitude and latitude [degree] if ``alt`` is ``FALSE`` (default).
        float or array, float or array, float or array
            West longitude, latitude [degrees] and altitude [km] if ``alt`` is ``TRUE``.

        """
        rh = np.sqrt(np.power(x, 2) + np.power(y, 2))
        if np.ndim(rh) == 0 and rh <= self.EPSILON:
            return (self.lon_w_0, self.lat_0, 0) if alt else (self.lon_w_0, self.lat_0)

        if np.ndim(rh) == 0:
            if rh > self.r and not alt:
                return None, None

            c = np.pi / 2 if rh > self.r else np.arcsin(rh / self.r)
        else:
            limb = rh > self.r
            c = np.pi / 2 * np.ones(np.shape(rh))
            c[~limb] = np.arcsin(rh[~limb] / self.r)

        cosc, sinc = np.cos(c), np.sin(c)

        lat = np.arcsin(cosc * self.slat0 + y / rh * sinc * self.clat0)
        if self.clat0 < self.EPSILON:
            lon_w = np.arctan2(x, np.invert(y)) if self.lat_0 >= 0 else \
                -np.arctan2(np.invert(x), y)
        else:
            lon_w = np.arctan2(sinc * x, rh * self.clat0 * cosc - self.slat0 * sinc * y)

        lon_w = (self.lon_w_0 - np.degrees(lon_w)) % 360
        lat = np.degrees(lat)

        if np.ndim(rh) > 0:
            cond = np.less_equal(rh, self.EPSILON, where=~np.isnan(rh)) | np.isnan(rh)
            lon_w[cond] = self.lon_w_0
            lat[cond] = self.lat_0

            # Remove limb data
            if not alt:
                lon_w[limb] = np.nan
                lat[limb] = np.nan

        if not alt:
            return lon_w, lat

        if np.ndim(rh) == 0:
            alt = 0 if rh <= self.r else (rh / self.r - 1) * self.radius
        else:
            alt = np.zeros(np.shape(rh))
            alt[limb] = (rh[limb] / self.r - 1) * self.radius

        return lon_w, lat, alt

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
        x, y = self.xy(*path.vertices.T, alt=path.alt) if hasattr(path, 'alt') else \
            self.xy(*path.vertices.T)

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

    def limb(self, npt=181):
        """Orthographic limb contour."""
        theta = np.linspace(0, 2 * np.pi, npt)
        return self.r * np.cos(theta), self.r * np.sin(theta)

    def grid(self, ax=None, color='gray',
             lw=.25, color_2='red', lw_2=.5,
             ticks=False):
        """Draw orthographic grid."""
        if ax is None:
            ax = plt.gca()

        ax.plot(*self.parallels(exclude=0), color=color, lw=lw)
        ax.plot(*self.parallels(0), color=color_2, lw=lw_2)

        ax.plot(*self.meridians(exclude=0), color=color, lw=lw)
        ax.plot(*self.meridians(0, lat_min=-90, lat_max=90), color=color_2, lw=lw_2)

        ax.plot(*self.limb(), color=color, lw=lw)

        if not ticks:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.axis('off')
