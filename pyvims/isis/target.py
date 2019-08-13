"""VIMS ISIS target module."""

import numpy as np

from .vectors import norm


def intersect(v, sc, r):
    """Sphere intersect with aim vector.

    Parameters
    ----------
    aim: [float, float, float]
        Aim J2000 unit vector in target frame.
    sc: [float, float, float]
        Sub-spacecraft position in target frame.
    r: float
        Body mean radius.

    Returns
    -------
    [float, float, float]
        Intersect J2000 position in target frame.

    """
    if np.ndim(sc) == 1 and np.ndim(v) == 1:
        dot = np.dot(sc, v)

    elif np.ndim(v) == 1:
        dot = np.dot(np.transpose(sc), v)

    elif np.ndim(sc) == 1:
        dot = np.dot(np.transpose(v), sc)

    elif np.shape(v)[1:] == np.shape(sc)[1:]:
        dot = np.sum(np.multiply(np.transpose(v), np.transpose(sc)), axis=1)

    else:
        raise ValueError('SC and aim vectors must have the same number of points.')

    # print(sc[:, 1333])
    # print(r)
    # print(norm(sc)[1333])
    # print(dot[1333])
    # print(np.subtract(norm(sc)**2, r**2))
    delta = np.subtract(dot**2, np.subtract(norm(sc)**2, r**2))

    if np.ndim(delta) > 0:
        delta[delta < 0] = 0
    elif delta < 0:
        delta = 0

    # return delta
    # return np.sqrt(-delta)
    lamb = np.multiply(dot + np.sqrt(delta), np.transpose([v]) if np.ndim(v) == 1 else v)

    return (np.transpose([sc]) if np.ndim(sc) == 1 else sc) - lamb
