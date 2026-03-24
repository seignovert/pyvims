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
        Angle mod 360° deg between -180° and 180°.

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
        Angle mod 360° deg between 0° and 360°.

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


def xyz(lon_w, lat, r=1):
    """Convert geographic coordinates in cartesian coordinates.

    Parameters
    ----------
    lon_w: float or numpy.array
        Point(s) west longitude [0°, 360°[.
    lat: float or numpy.array
        Point(s) latitude [-90°, 90°].
    r: float or numpy.array, optional
        Point(s) distance/altitude [km].

    Return
    ------
    [float, float, float]
        Cartesian coordinates.

    Examples
    --------
    >>> xyz(0, 0)
    [1, 0, 0]
    >>> xyz(90, 0)
    [0, -1, 0]
    >>> xyz(315, 0)
    [0.707..., 0.707..., 0]
    >>> xyz(0, 45)
    [0.707..., 0, 0.707...]

    """
    _lon_w, _lat = np.radians([lon_w, lat])
    clon_e, clat = np.cos([-_lon_w, _lat])
    slon_e, slat = np.sin([-_lon_w, _lat])
    return r * np.array([clat * clon_e, clat * slon_e, slat])


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
        return np.sum(np.multiply(np.transpose(v1), np.transpose(v2)), axis=-1)

    raise ValueError('The two vectors must have the same number of points.')


def angle(v1, v2):
    """Angular separation between two vectors."""
    dot = vdot(hat(v1), hat(v2))

    if np.ndim(dot) == 0 and dot > 1:
        return 0

    if np.ndim(dot) > 0:
        dot[dot > 1] = 1

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
    """Calculate distance between 2 points on a sphere.

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
    lambda_1, phi_1 = np.radians([lon_1, lat_1])
    lambda_2, phi_2 = np.radians([lon_2, lat_2])
    return 2 * r * np.arcsin(np.sqrt(
        hav(phi_2 - phi_1) + np.cos(phi_1) * np.cos(phi_2) * hav(lambda_2 - lambda_1)
    ))


def areaquad(lon_0, lat_0, lon_1, lat_1, r=1):
    """Calculate the surface area of a quadrangle on a sphere.

    The surface area on a sphere bounded by two meridians and two parallels.

    Parameters
    ----------
    lon_0: float or array
        Start meridians (deg).
    lon_1: float or array
        Stop meridians (deg).
    lat_0: float or array
        Start parallele (deg).
    lat_1: float or array
        Stop parallele (deg).
    r: float, optional
        Sphere radius.

    Returns
    -------
    The quadrangle surface (in `r` units squared).

    """
    dlambda = np.radians(lon_1 - lon_0)
    sin_phi_0, sin_phi_1 = np.sin(np.radians([lat_0, lat_1]))
    return np.abs(r ** 2 * dlambda * (sin_phi_1 - sin_phi_0))


def azimuth(inc, eme, phase):
    """Local azimuth angle between the sun and the observer.

    Parameters
    ----------
    inc: float or numpy.ndarray
        Incidence angle (degrees).
    eme: float or numpy.ndarray
        Emergence angle (degrees).
    phase: float or numpy.ndarray
        Phase angle (degrees).

    Returns
    -------
    float or numpy.ndarray
        Local azimuth angle (degrees).

    Raises
    ------
    ValueError
        If the inputs do not have the same dimension.

    """
    if not np.shape(inc) == np.shape(eme) == np.shape(phase):
        raise ValueError(f'Incidence {np.shape(inc)}, emergence {np.shape(eme)} '
                         f'and phase {np.shape(phase)} do not have the same dimension.')

    if np.ndim(inc) == 0 and (inc == 0 or eme == 0):
        return 0

    i, e, p = np.radians([inc, eme, phase])

    azi = np.cos(p) - np.cos(i) * np.cos(e)

    if np.ndim(inc) == 0:
        azi /= np.sin(i) * np.sin(e)
    else:
        azi = np.divide(azi, np.sin(i) * np.sin(e),
                        out=np.ones_like(i),
                        where=(np.not_equal(inc, 0) & np.not_equal(eme, 0)))

    return np.degrees(np.arccos(np.clip(azi, -1, 1)))
