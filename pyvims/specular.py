"""Specular reflexion module."""

import numpy as np

from .vectors import hat, norm, lonlat
from .quaternions import q_rot


SUN_RADIUS = 6.955e5  # km


def specular_angle(beta, dist, radius, debug=False):
    '''Find specular angle with SS in the SS-O-SC plane.

    Parameters
    ----------
    beta: float
        Angle between SS and SC (radians).
    radius: float
        Target radius (same units as :py:attr:`dist`).
    dist: float
        Distance between the target center
        and spacecraft position (same units as :py:attr:`radius`).
    debug: bool, optional
        debug output debugger. Disable by default.

    Return
    ------
    float
        Specular angle (radians).

    Raises
    ------
    ValueError
        If not roots are found or not roots correspond
        to the expected geometry.

    '''
    r_d = radius / dist

    sin_beta = np.sin(beta)

    b = - r_d * sin_beta
    c = np.power(r_d / 2, 2) - 1
    d = r_d / 2 * sin_beta
    e = np.power(sin_beta / 2, 2)

    roots = np.roots([1, b, c, d, e])

    if debug:
        print(f'<SPECULAR ANGLE> Roots: {roots}')

    cond = (np.abs(roots.imag) < 1e-6) & (np.abs(roots) <= 1)

    if not cond.any():
        raise ValueError(f'No accepted root found: {roots}')

    roots = roots.real[cond]

    alphas = np.arcsin(roots)
    betas = 2 * alphas - np.arcsin(r_d * roots)
    diff = np.abs(
        np.abs(np.cos(beta) - np.cos(betas))
        + np.abs(np.sin(beta) - np.sin(betas)))

    if debug:
        print(f'<SPECULAR ANGLE> Alphas: {np.degrees(alphas)}')
        print(f'<SPECULAR ANGLE> Betas: {np.degrees(betas)}')

    if np.min(diff) > 1e-2:
        raise ValueError(f'No root match the expected geometry.\n'
                         f' - Output betas: {np.degrees(betas)} deg.\n'
                         f' - Expected: {np.degrees(beta)} deg')

    return alphas[np.argmin(diff)]


def specular_location(sc, sun, radius):
    """Locate specular point on the ground.

    Parameters
    ----------
    sc: [float, float, float]
        Sub-spacecraft vector.
    sun: [float, float, float]
        Sub-solar vector.
    radius: float
        Planet radius (same units as :py:attr:`sc`).

    Return
    ------
    (float, float, float)
        Specular point west longitude, latitude and angle (deg).

    """
    beta = np.arccos(np.dot(hat(sc), hat(sun)))
    try:
        alpha = specular_angle(beta, norm(sc), radius)
    except ValueError:
        return np.array([np.nan, np.nan, None])

    c, s = np.cos(alpha / 2), np.sin(alpha / 2)
    n = hat(np.cross(sun, sc))

    v = q_rot([c, *(s * n)], sun)
    return np.array([*lonlat(v), np.degrees(alpha)])


def specular_footprint(sc, ss, radius, npt=33):
    """Calculate the specular footprint of the sun on the surface."""
    theta = np.linspace(0, 2 * np.pi, npt)
    ct = np.transpose([np.cos(theta)])
    st = np.transpose([np.sin(theta)])

    x = hat(np.cross(ss, np.cross(ss, [0, 0, 1])))
    y = hat(np.cross(ss, x))

    ss_sun = ss + SUN_RADIUS * (x * ct + y * st)

    lons = []
    lats = []
    for sun in ss_sun:
        lon, lat, _ = specular_location(sc, sun, radius)
        lons.append(lon)
        lats.append(lat)

    return np.array([lons, lats])
