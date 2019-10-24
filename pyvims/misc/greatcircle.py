"""Great circle module."""

import numpy as np

from ..vectors import angle, lonlat, xyz


def great_circle_arc(lon1, lat1, lon2, lat2, npt=361):
    """Great circle arc coordinates between 2 anchor points.

    Use Slerp interpolation.

    Parameters
    ----------
    lon1: float
        West longitude of the first point (degree).
    lat1: float
        Latitude of the first point (degree).
    lon2: float
        West longitude of the second point (degree).
    lat2: float
        Latitude of the second point (degree).
    npt: int, option
        Number of points in the great circle.

    Raises
    ------
    ValueError
        If the two longitudes are on the same meridian (±180°).

    """
    if (lon1 - lon2) % 180 == 0:
        raise ValueError('Infinity of solutions. '
                         'Longitudes 1 and 2 are on the same meridian (±180°).')

    pt1 = xyz(lon1, lat1)
    pt2 = xyz(lon2, lat2)
    omega = np.radians(angle(pt1, pt2))
    s = np.sin(omega)

    t = np.transpose([np.linspace(0, 1, npt)])
    v = (np.sin((1 - t) * omega) * pt1 + np.sin(t * omega) * pt2) / s

    return lonlat(v.T)


def great_circle(lon, lon1, lat1, lon2, lat2):
    """Great circle latitude through 2 points.

    Source: https://edwilliams.org/avform.htm

    Parameters
    ----------
    lon: float or numpy.array
        Input west longitude on the great circle (degree).
    lon0: float
        West longitude of the first point (degree).
    lat0: float
        Latitude of the first point (degree).
    lon1: float
        West longitude of the second point (degree).
    lat1: float
        Latitude of the second point (degree).

    Returns
    -------
    float or numpy.array
        Great circle latitude for the longitude provided.

    Raises
    ------
    ValueError
        If the two longitudes are on the same meridian (±180°).

    """
    if (lon1 - lon2) % 180 == 0:
        raise ValueError('Infinity of solutions. '
                         'Longitudes 1 and 2 are on the same meridian (±180°).')

    lon = np.asarray(lon)
    s1, s2 = np.sin(np.radians([lon - lon1, lon - lon2]))
    s12 = np.sin(np.radians(lon1 - lon2))
    t1, t2 = np.tan(np.radians([lat1, lat2]))
    return np.degrees(np.arctan((t1 * s2 - t2 * s1) / s12))


def great_circle_pole_pts(lon_p, lat_p):
    """Find two orthogonal points on the great circle from its polar axis.

    Parameters
    ----------
    lon_p: float
        Polar axis west longitude (degree).
    lat_p: float
        Polar axis latitude (degree).

    Returns
    -------
    float
        West longitude of first orthogonal point (with the same longitude).
    float
        Latitude of first orthogonal point (with the same longitude).
    float
        West longitude of second orthogonal point (crossing the equator).
    float
        Latitude of second orthogonal point (crossing the equator).

    """
    lon1, lat1 = lon_p, lat_p - 90 if lat_p >= 0 else lat_p + 90
    lon2, lat2 = lon_p - 90 if lon_p >= 90 else lon_p + 90, 0
    return lon1, lat1, lon2, lat2


def great_circle_pole(lon, lon_p, lat_p):
    """Great circle latitude from its polar axis.

    Parameters
    ----------
    lon: float or numpy.array
        Input west longitude on the great circle (degree).
    lon_p: float
        Polar axis west longitude (degree).
    lat_p: float
        Polar axis latitude (degree).

    Returns
    -------
    float or numpy.array
        Great circle latitude for the longitude provided.

    """
    return great_circle(lon, *great_circle_pole_pts(lon_p, lat_p))
