"""Pyplot Sky projection."""

import numpy as np

from ..interp import cube_interp
from ..vectors import deg180, deg360


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
    (c_r, s_r), (c_d, s_d), (c_t, s_t) = cs(ra), cs(dec), cs(twist / 2)

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


def xy(ra, dec, m_sky):
    """Project RA/DEC pointing vector on the sky tangant plane."""
    x, y, z = np.dot(m_sky, xyz(ra, dec))
    return y / x, z / x


def radec(x, y, m_sky):
    """Project vector from sky tangant plane to RA/DEC coordinates."""
    u = np.array([np.ones(np.shape(x)), x, y])
    u = u / np.linalg.norm(u, axis=0)
    v = np.dot(np.transpose(m_sky), u)
    ra = np.degrees(np.arctan2(v[1], v[0]))
    dec = np.degrees(np.arcsin(v[2]))
    return np.array([deg360(ra), deg180(dec)])


def sky_pixels(radec, m_sky):
    """Pixel positions on the FOV tangent plane.

    Parameters
    ----------
    radec: np.array
        2D array pixel RA/DEC coordinates.
    m_sky: np.array
        Pointing rotation matrix.

    Returns
    -------
    np.array
        Pixels X/Y positions.

    """
    s = np.shape(radec)
    npix = int(np.product(s) / 2)
    pix = xy(*np.reshape(radec, (2, npix)), m_sky)
    return np.reshape(pix, s)


def sky_contour(radec, m_sky):
    """Contour positions on the FOV tangent plane

    Parameters
    ----------
    radec: np.array
        2D array contour RA/DEC coordinates.
    m_sky: np.array
        Pointing rotation matrix.

    Returns
    -------
    np.array
        Contour X/Y positions.

    """
    return xy(*radec, m_sky)


def sky_grid(grid, m_sky):
    """Interpolated sky grid.

    Parameters
    ----------
    grid: np.array
        Interpolation grid.
    m_sky: np.array
        Pointing rotation matrix.

    Returns
    -------
    np.array
        Grid RA/DEC coordinates.

    """
    s = np.shape(grid)
    npix = int(np.product(s) / 2)
    x, y = np.reshape(grid, (2, npix))
    return radec(x, y, m_sky).reshape(s)


def sky_interp(pixels, data, contour, n=512, method='cubic'):
    """VIMS pixels data interpolated on the sky.

    Parameters
    ----------
    pixels: np.array
        Pixels X/Y positions.
    data: np.array
        2D/3D data pixels values.
    contour: np.array
        Contour X/Y positions.
    m_sky: np.array
        Pointing rotation matrix.
    n: int, optional
        Number of pixel for the grid interpolation.
    method: str, optional
        Interpolation method

    """
    # Plane resolution
    res = np.min(np.max(contour, axis=1) - np.min(contour, axis=1)) / n

    # Interpolate data (with mask)
    z, grid, extent = cube_interp(pixels, data, res, contour, method=method)

    return z, grid, extent


def sky_cube(c, index, twist=0, n=512, interp='cubic'):
    """VIMS cube projected on the sky.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to interpolate.
    index: int, float, str, list, tuple
        VIMS band or wavelength to plot.
    twist: float, optional
        Camera poiting twist angle (degree).
    n: int, optional
        Number of pixel for the grid interpolation.
    interp: str, optional
        Interpolation method

    """
    # Pixel data
    data = c[index]

    # Mean pointing rotation matrix
    m_sky = rot_sky(*c.pointing[:2], twist)

    # Pixel positions on the FOV tangent plane
    pixels = sky_pixels(c.sky, m_sky)

    # Contour positions on the FOV tangent plane
    contour = sky_contour(c.csky, m_sky)

    # Interpolate data (with mask)
    z, grid, extent = sky_interp(pixels, data, contour, n=n, method=interp)

    return z, grid, extent, pixels, contour, sky_grid(grid, m_sky)
