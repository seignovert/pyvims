"""Quaternions module."""

import numpy as np

from .vectors import hat


def is_rot(m):
    """Check if the matrix is a rotation matrix.

    Rotation matrix are defined as orthogonal matrix
    with a determinant of 1.

    Parameters
    ----------
    m: np.array
        Input matrix.

    Returns
    -------
    bool
        ``TRUE`` if the matrix is a rotation matrix.

    """
    if np.ndim(m) != 2:
        return False

    shape = np.shape(m)
    if shape[0] != shape[1]:
        return False

    is_ortho = np.allclose(np.dot(m, np.transpose(m)), np.identity(shape[0], np.float))
    is_det_1 = np.allclose(np.linalg.det(m), 1)
    return is_ortho and is_det_1


def m2q(m):
    """Convert rotation matrix into SPICE quaternion.

    Parameters
    ----------
    m: np.array
        3x3 rotation matrix.

    Returns
    -------
    np.array
        SPICE quaternion.

    Raises
    ------
    ValueError
        If the rotation matrix does not contains 9 elements.
    ValueError
        If the matrix provided is not a rotation matrix.
        See also :py:func:`is_rot`.

    """
    if np.ndim(m) == 1:
        if np.shape(m)[0] != 9:
            raise ValueError('Rotation matrix must have 9 elements.')
        m = np.reshape(m, (3, 3))

    if not is_rot(m):
        raise ValueError('The matrix provided is not a rotation matrix.')

    m = np.asarray(m)
    t = m.trace()

    s0 = 1 + t
    s1 = 1 - t + 2 * m[0, 0]
    s2 = 1 - t + 2 * m[1, 1]
    s3 = 1 - t + 2 * m[2, 1]

    if s0 >= 1:
        q0 = np.sqrt(s0 / 4)
        factor = 1 / (4 * q0)

        q1 = (m[2, 1] - m[1, 2]) * factor
        q2 = (m[0, 2] - m[2, 0]) * factor
        q3 = (m[1, 0] - m[0, 1]) * factor

    elif s1 >= 1:
        q1 = np.sqrt(s1 / 4)
        factor = 1 / (4 * q1)

        q0 = (m[2, 1] - m[1, 2]) * factor
        q2 = (m[0, 1] + m[1, 0]) * factor
        q3 = (m[0, 2] + m[2, 0]) * factor

    elif s2 >= 1:
        q2 = np.sqrt(s2 / 4)
        factor = 1 / (4 * q2)

        q0 = (m[0, 2] - m[2, 0]) * factor
        q1 = (m[0, 1] + m[1, 0]) * factor
        q3 = (m[1, 2] + m[2, 1]) * factor

    else:
        q3 = np.sqrt(s3 / 4)
        factor = 1 / (q3 * 4)

        q0 = (m[1, 0] - m[0, 1]) * factor
        q1 = (m[0, 2] + m[2, 0]) * factor
        q2 = (m[1, 2] + m[2, 1]) * factor

    q = np.array([q0, q1, q2, q3])

    return np.sign(q0) * hat(q)


def q2m(q):
    """Convert SPICE quaternion in rotation matrix.

    Parameters
    ----------
    m: np.array
        SPICE quaternion.

    Returns
    -------
    np.array
        3x3 rotation matrix.

    Raises
    ------
    ValueError
        If the quaternion provided does not contains 4 elements.

    """
    if np.shape(q)[0] != 4:
        raise ValueError('Quaternion must have 4 elements.')

    q0, q1, q2, q3 = hat(q)
    return np.array([[
        1 - 2 * (q2 * q2 + q3 * q3),
        2 * (q1 * q2 - q0 * q3),
        2 * (q1 * q3 + q0 * q2),
    ], [
        2 * (q1 * q2 + q0 * q3),
        1 - 2 * (q1 * q1 + q3 * q3),
        2 * (q2 * q3 - q0 * q1),
    ], [

        2 * (q1 * q3 - q0 * q2),
        2 * (q2 * q3 + q0 * q1),
        1 - 2 * (q1 * q1 + q2 * q2),
    ]])


def q2mt(q):
    """Convert SPICE quaternion in transposed rotation matrix.

    Parameters
    ----------
    m: np.array
        SPICE quaternion.

    Returns
    -------
    np.array
        3x3 rotation matrix.

    Raises
    ------
    ValueError
        If the quaternion provided does not contains 4 elements.

    """
    if np.shape(q)[0] != 4:
        raise ValueError('Quaternion must have 4 elements.')

    q0, q1, q2, q3 = hat(q)
    return np.array([[
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


def q_mult(q0, q1):
    """Multiply quaternions.

    Each quaternion can be written as:

        Q = s + v
        s = q0
        v = [q1, q2, q3]

    Then:

        Q1 * Q2 = (s1 * s2 - <v1, v2>) + [s1 * v2 + s2 * v1 + (v1 x v2)]

    With <v1, v2> the dot product and (v1 x v2) the cross product.

    Parameters
    ----------
    q0: np.array
        First quaternion(s).
    q1: np.array
        Second quaternion(s).

    Returns
    -------
    np.array
        SPICE quaternion(s).

    """
    if np.ndim(q0) == 1:
        s0, v0 = np.array([q0[0]]), np.transpose([q0[1:]])
    else:
        s0, v0 = q0[0, :], np.array(q0[1:, :])

    if np.ndim(q1) == 1:
        s1, v1 = np.array([q1[0]]), np.transpose([q1[1:]])
    else:
        s1, v1 = q1[0, :], np.array(q1[1:, :])

    s = s0 * s1

    dot = np.dot(v0.T, v1)
    s -= dot.flatten() if 1 in dot.shape else dot.diagonal()

    v = s0 * v1 + s1 * v0 + np.cross(v0.T, v1.T).T

    return np.array([s, v[0], v[1], v[2]]) if s.shape[0] != 1 else \
        np.hstack([s, v[0], v[1], v[2]])


def q_rot(q, v):
    """Vector rotation based on quaternion.

    See :py:func:`q_rot_t` for the inverse rotation.

    Parameters
    ----------
    q: np.array
        Rotation quaternion(s).
    v: np.array
        Vector(s) to rotate.

    Returns
    -------
    np.array
        Rotated vector(s).

    """
    if np.ndim(q) == 1:
        return np.dot(q2m(q), v)

    if np.ndim(v) == 1:
        return np.dot(np.transpose(v), q2m(q))

    if np.shape(q)[1:] != np.shape(v)[1:]:
        raise ValueError('Quaternion and vector must have the same number of points.')

    return np.sum(np.multiply(q2m(q), v), axis=1)


def q_rot_t(q, v):
    """Reverse vector rotation based on quaternion.

    Inverse rotation of :py:func:`q_rot`.

    Parameters
    ----------
    q: np.array
        Rotation quaternion(s).
    v: np.array
        Vector(s) to rotate.

    Returns
    -------
    np.array
        Rotated vector(s).

    """
    if np.ndim(q) == 1:
        return np.dot(q2mt(q), v)

    if np.ndim(v) == 1:
        return np.dot(np.transpose(v), q2mt(q))

    if np.shape(q)[1:] != np.shape(v)[1:]:
        raise ValueError('Quaternion and vector must have the same number of points.')

    return np.sum(np.multiply(q2mt(q), v), axis=1)


def q_interp(q0, q1, t, threshold=0.9995):
    """Quaternions interpolation (Slerp method).

    If the inputs are too close for comfort, linearly
    interpolate and normalize the result.

    Parameters
    ----------
    q0: np.array
        First quaternion (``t=0``).
    q1: np.array
        Last quaternion (``t=1``).
    t: float or np.array
        Parametric value(s) between the first and last quaternion.
    threshold: float
        Dot production threshold 0.9995

    Returns
    -------
    np.array
        Interpolated quaternion(s).

    """
    is_single = isinstance(t, (int, float))
    t = np.asarray([t] if is_single else t)
    q0 = np.asarray(q0)
    q1 = np.asarray(q1)

    dot = np.sum(q0 * q1)

    if (dot < 0):
        q1 = -q1
        dot = -dot

    if (dot > threshold):
        result = q0[np.newaxis, :] + t[:, np.newaxis] * (q1 - q0)[np.newaxis, :]
        return hat(result.T).T

    theta_0 = np.arccos(dot)
    sin_theta_0 = np.sin(theta_0)

    theta = theta_0 * t
    sin_theta = np.sin(theta)

    s0 = np.cos(theta) - dot * sin_theta / sin_theta_0
    s1 = sin_theta / sin_theta_0

    q = (s0[:, np.newaxis] * q0[np.newaxis, :]) + (s1[:, np.newaxis] * q1[np.newaxis, :])
    return q.flatten() if is_single else q
