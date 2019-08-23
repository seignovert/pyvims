"""Pyplot Sky projection."""

import numpy as np


def cs(theta):
    '''COS and SIN values.

    Parameters
    ----------
    theta: float
        Input angle (deg).

    Returns
    -------
    (float, float)
        Cosinus and sinus of the input angle.

    '''
    rad_theta = np.radians(theta)
    return np.array([np.cos(rad_theta), np.sin(rad_theta)])


def rot_sky(ra, dec, twist):
    """Calculate sky pointing rotation matrix."""
    (c_r, s_r), (c_d, s_d), (c_t, s_t) = cs(ra), cs(dec), cs(twist/2)

    m1 = np.array([
        [c_d, 0, s_d],
        [0, 1, 0],
        [-s_d, 0, c_d],
    ])

    m2 = np.array([
        [c_r, s_r, 0],
        [-s_r, c_r, 0],
        [0, 0, 1],
    ])

    q0 = c_t
    q1 = s_t * c_d * c_r
    q2 = s_t * c_d * s_r
    q3 = s_t * s_d

    m3 = np.array([[
        1 - 2 * (q2 * q2 + q3 * q3),
        2 * (q1 * q2 + q0 * q3),
        2 * (q1 * q3 - q0 * q2),
    ], [
        2 * (q1 * q2 - q0 * q3),
        1 - 2 * (q1 * q1 + q3 * q3),
        2 * (q2 * q3 + q0 * q1),
    ], [

        2 * (q1 * q3 + q0 * q2),
        2 * (q2 * q3 - q0 * q1),
        1 - 2 * (q1 * q1 + q2 * q2),
    ]])

    return np.dot(m1, np.dot(m2, m3))


def xyz(ra, dec):
    """Convert RA/DEC pointing into XYZ coordinates."""
    (c_r, s_r), (c_d, s_d) = cs(ra), cs(dec)
    return np.array([
        c_r * c_d,
        s_r * c_d,
        s_d
    ])


def xy(ra, dec, sky):
    """Project RA/DEC pointing vector on the sky tangant plane."""
    x, y, z = np.dot(sky, xyz(ra, dec))
    return y / x, z / x


def radec(x, y, sky):
    """Project vector from sky tangant plane to RA/DEC coordinates."""
    u = np.array([np.ones(np.shape(x)), x, y])
    u = u / np.linalg.norm(u)
    v = np.dot(np.transpose(sky), u)
    ra = np.arctan2(v[1], v[0])
    dec = np.arcsin(v[2])
    return np.degrees([ra, dec])
