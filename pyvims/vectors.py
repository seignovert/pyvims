"""Vector module."""

import numpy as np


def deg180(ang):
    """Restrict angle in [-180; 180[ degrees range.

    Parameters
    ----------
    ang: float
        Angle in degrees.

    Return
    ------
    float
        Angle mod 360º deg between -180º and 180º.

    Example
    -------
    >>> deg180(0)
    0
    >>> deg180(360)
    0
    >>> deg180(270)
    -90
    >>> deg180(-90)
    -90
    >>> deg180(-270)
    90

    """
    return (np.asarray(ang) + 180) % 360 - 180


def deg360(ang):
    """Restrict angle in [0; 360[ degrees range.

    Parameters
    ----------
    ang: float
        Angle in degrees.

    Return
    ------
    float
        Angle mod 360º deg between 0º and 360º.

    Example
    -------
    >>> deg360(0)
    0
    >>> deg360(360)
    0
    >>> deg360(-90)
    270
    >>> deg360(270)
    270
    >>> deg360(-270)
    90

    """
    return np.asarray(ang) % 360


def lonlat(xyz):
    """Convert cartesian coordinates into geographic coordinates.

    Parameters
    ----------
    xyz: numpy.array
        XYZ cartesian vector.

    Return
    ------
    (float, float)
        Longitude West (0 to 360) and Latitude North (deg).

    Examples
    --------
    >>> lonlat([1, 0, 0])
    (0, 0)
    >>> lonlat([0, 1, 0])
    (270, 0)
    >>> lonlat([1, 1, 0])
    (315, 0)
    >>> lonlat([1, 0, 1])
    (0, 45)

    """
    x, y, z = xyz
    lon_w = deg360(np.degrees(-np.arctan2(y, x)))
    lat = np.degrees(np.arcsin(z / norm(xyz)))
    return np.array([lon_w, lat])


def radec(j2000):
    """Convert RA/DEC pointing in cartesian coordinates in J2000 frame.

    Parameters
    ----------
    np.array
        3xn XYX vector in J2000 frame.

    Return
    ------
    ra: float
        Right ascension (deg).
    dec: float
        Declination (deg).

    Examples
    --------
    >>> radec([1, 0, 0])
    (0, 0)
    >>> radec([0, 1, 0])
    (90, 0)
    >>> radec([0, 0, 1])
    (0, 90)

    """
    lon_w, lat = lonlat(j2000)
    return np.array([deg360(-lon_w), lat])


def norm(v):
    """Vector norm.

    Parameters
    ----------
    v: np.array
        Input vector to measure(s).

    Returns
    -------
    float or np.array
        Input vector norm(s).

    Examples
    --------
    >>> norm([1, 0, 0])
    1
    >>> norm([1, 1, 1])
    1.732050...

    """
    return np.linalg.norm(v, axis=0)


def hat(v):
    """Normalize vector.

    Parameters
    ----------
    v: np.array
        Input vector to normalize.

    Returns
    -------
    np.array
        Normalize input vector.

    Examples
    ---------
    >>> hat([1, 0, 0])
    array([1., 0., 0.])
    >>> hat([1, 1, 1])
    array([0.577..., 0.577..., 0.577...])

    """
    return np.asarray(v) / norm(v)


def v_max_dist(v):
    """Find the two vector with the largest distance.

    Parameters
    ----------
    v: np.array
        3xN array of 3D vectors.

    Returns
    -------
    (int, int)
        Tuple of the two vectors with the largest
        distance between them.

    """
    dist = np.sum(np.power(np.subtract(
        v.T[np.newaxis, :], v.T[:, np.newaxis]), 2), axis=2)
    return np.unravel_index(np.argmax(dist), dist.shape)


def vdot(v1, v2):
    """Dot product between two vectors."""
    if np.ndim(v1) == 1 and np.ndim(v2) == 1:
        return np.dot(v1, v2)

    if np.ndim(v1) == 1:
        return np.dot(np.transpose(v2), v1)

    if np.ndim(v2) == 1:
        return np.dot(np.transpose(v1), v2)

    if np.shape(v1)[1:] == np.shape(v2)[1:]:
        return np.sum(np.multiply(np.transpose(v1), np.transpose(v2)), axis=1)

    raise ValueError('The two vectors must have the same number of points.')


def angle(v1, v2):
    """Angular separation between two vectors."""
    dot = vdot(hat(v1), hat(v2))
    return np.degrees(np.arccos(dot))


def hav(theta):
    """Trigonometric half versine function.

    Parameters
    ----------
    theta: float or np.array
        Angle in radians

    Returns
    -------
    float or np.array
        Half versine value.

    """
    return .5 * (1 - np.cos(theta))


def hav_dist(lon_1, lat_1, lon_2, lat_2, r=1):
    """Calculate distance between 2 points on a spehere.

    Parameters
    ----------
    lon_1: float or np.array
        Point 1 west longitude (degree).
    lat_1: float or np.array
        Point 1 north latitude (degree).
    lon_2: float or np.array
        Point 2 west longitude (degree).
    lat_2: float or np.array
        Point 2 north latitude (degree).
    r: float, optional
        Planet radius.

    Returns
    -------
    float or np.array
        Haversine distance between the 2 points.

    """
    phi_1, lambda_1, phi_2, lambda_2 = np.radians([lon_1, lat_1, lon_2, lat_2])
    return 2 * r * np.arcsin(np.sqrt(
        hav(phi_2 - phi_1) + np.cos(phi_1) * np.cos(phi_2) * hav(lambda_2 - lambda_1)
    ))
