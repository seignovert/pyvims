"""VIMS ISIS target module."""

import numpy as np

from .vectors import norm, vdot


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
    dot = vdot(sc, v)

    delta = np.subtract(dot**2, np.subtract(norm(sc)**2, r**2))

    if np.ndim(delta) > 0:
        delta[delta < 0] = 0
    elif delta < 0:
        delta = 0

    lamb = np.multiply(dot + np.sqrt(delta), np.transpose([v]) if np.ndim(v) == 1 else v)

    return (np.transpose([sc]) if np.ndim(sc) == 1 else sc) - lamb
