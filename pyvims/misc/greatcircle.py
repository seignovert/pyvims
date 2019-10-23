"""Great circle module."""

import numpy as np

from ..vectors import angle, lonlat, xyz


def great_circle(lon0, lat0, lon1, lat1, npt=361):
    """Great circle coordinates based on 2 anchor points.

    Use Slerp interpolation.

    Parameters
    ----------
    lon0: float
        West longitude of the first point (degree).
    lat0: float
        Latitude of the first point (degree).
    lon1: float
        West longitude of the second point (degree).
    lat1: float
        Latitude of the second point (degree).
    npt: int, option
        Number of points in the great circle.

    """
    pt0 = xyz(lon0, lat0)
    pt1 = xyz(lon1, lat1)
    omega = np.radians(angle(pt0, pt1))
    s = np.sin(omega)

    t = np.transpose([np.linspace(0, 1, npt)])
    v = (np.sin((1 - t) * omega) * pt0 + np.sin(t * omega) * pt1) / s

    return lonlat(v.T)
