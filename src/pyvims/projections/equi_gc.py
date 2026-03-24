"""Equirectangular projection module."""

import numpy as np

from matplotlib.path import Path

from .equi import Equirectangular as EquirectangularProjection
from ..misc.greatcircle import great_circle_arc


class Equirectangular(EquirectangularProjection):
    """Equirectangular projection with great circle object.

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

    See Also
    --------
    pyvims.projections.equi.Equirectangular
    pyvims.projections.__main__.GroundProjection

    """

    def __init__(self, lon_w_0=180, lat_0=0, lat_ts=0, target=None, radius=None,
                 npt_gc=8):
        self.lon_w_0 = lon_w_0
        self.lat_0 = lat_0
        self.target = target
        self.radius = radius
        self.lat_ts = lat_ts
        self.npt_gc = npt_gc

    def _vc(self, path):
        """Get projected vertices and codes (and close the polygon if needed).

        Add new intermediate points along great circles to get defined the shape
        of the polygons.

        Parameters
        ----------
        path: matplotlib.path.Path
            Matplotlib path in west-longitude and latitude coordinates.

        Returns
        -------
        [float], [float], [int]
            X and Y vertices and path code.

        """
        lon_w, lat = path.vertices.T

        # Add codes if missing
        if path.codes is None:
            codes = [Path.MOVETO] + [Path.LINETO] * (len(lon_w) - 2) + [Path.CLOSEPOLY]
        else:
            codes = path.codes

        # Close the path
        if lon_w[0] != lon_w[-1] or lat[0] != lat[-1]:
            lon_w = np.concatenate([lon_w, [lon_w[0]]])
            lat = np.concatenate([lat, [lat[0]]])

            if codes[-1] == Path.CLOSEPOLY:
                codes = np.concatenate([codes[:-1], [Path.LINETO, Path.CLOSEPOLY]])
            else:
                codes = np.concatenate([codes, [Path.CLOSEPOLY]])

        nv = len(lon_w) - 1

        vertices = [
            (_lon_w, _lat)
            for i in range(nv)
            for _lon_w, _lat in great_circle_arc(
                lon_w[i], lat[i], lon_w[i + 1], lat[i + 1], npt=self.npt_gc).T[:-1]
        ] + [(lon_w[-1], lat[-1])]

        gc_codes = np.concatenate(
            [
                [code] + (self.npt_gc - 2) * [Path.LINETO]
                for code in codes[:-1]
            ]
            + [[Path.CLOSEPOLY]])

        return np.transpose(self.xy(*np.transpose(vertices))), gc_codes
