# -*- coding: utf-8 -*-
"""Map footprint module."""

import numpy as np

from shapely.geometry import Polygon, Point


def R(lon, lat):
    """Pointing matrix withou rotation.

    Parameters
    ----------
    lon: float
        Pointing longitude (degE)
    lat: float
        Pointing latitude (degN)

    Return
    ------
    numpy.array
        Rotation matrix.

    """
    rlon = np.radians(lon)
    rlat = np.radians(90 - lat)
    cz, sz = np.cos(rlon), np.sin(rlon)
    cy, sy = np.cos(rlat), np.sin(rlat)

    return np.array([
        [cy * cz, -sz, sy * cz],
        [cy * sz, cz, sy * sz],
        [-sy, 0, cy],
    ])


def great_circle(lon, lat, npt=361):
    """Great circle coordinates.

    The corrdinates are sorted by longitude.

    Parameters
    ----------
    lon: float
        Pointing longitude (degE)
    lat: float
        Pointing latitude (degN)
    npt: int, optional
        Numver

    Return
    ------
    float, float
        Great circle latitude and longitude.

    """

    theta = np.radians(np.linspace(0, 360, npt))
    M = np.array([np.cos(theta), np.sin(theta), 0 * theta])
    x, y, z = np.dot(R(lon, lat), M)

    lonlat = np.transpose([np.degrees(np.arctan2(y, x)),
                           np.degrees(np.arcsin(z))])

    return lonlat[lonlat[:, 0].argsort()].T


def pt_circle(pt0, pt1):
    """Find point intersection on a unitary circle.
                                \
       +===========+------------>|
                                /
      pt0         pt1           pt

    """
    x0, y0, _ = pt0
    x1, y1, _ = pt1

    if x0 == x1:
        return x0, (1 if y1 >= y0 else -1) * np.sqrt(1 - x0**2)

    a = (y1 - y0) / (x1 - x0)
    b = y0 - a * x0

    if a**2 - b**2 + 1 < 0:
        raise ValueError('No intersection')

    x = (-np.sqrt(a**2 - b**2 + 1) - a*b) / (1 + a**2)

    if not (x0 <= x1 and x1 <= x) and not (x <= x1 and x1 <= x0):
        x = (np.sqrt(a**2 - b**2 + 1) - a*b) / (1 + a**2)

    y = a * x + b

    return x, y


def corner(pt0, pt1, pt2, pt3, dth=1):
    """Calculate missing corner on the limb.

    Points location:

        x    +---+
            2   3
        + 1
        |
        + 0

    """
    p1 = pt_circle(pt0, pt1)
    p2 = pt_circle(pt3, pt2)

    alpha = np.arccos(np.dot(p1, p2))

    ntheta = max([int(alpha/np.radians(dth)), 2])
    theta = np.arctan2(p1[1], p1[0]) - np.linspace(0, alpha, ntheta)

    return np.cos(theta), np.sin(theta), 0*theta


def lonlat2xyz(lon, lat, M):
    """Convert latitude/longitude coordinates into X/Y/Z coordinates.

    Parameters
    ----------
    lon: [float]
        Longitude on the globe.
    lat: [float]
        Latitude on the globe.
    M: numpy.array
        FOV rotation matrix.

    Return
    ------
    [float, float, float]
        X/Y/Z coordinates in Cassini FOV plane.

    """
    r = np.radians([lon, lat])
    (clon, clat), (slon, slat) = np.cos(r), np.sin(r)
    xyz = np.array([clon * clat, slon * clat, slat])
    return np.dot(M.T, xyz)


def xyz2lonlat(xyz, M):
    """Convert X/Y/Z coordinates into latitude/longitude coordinates.

    Parameters
    ----------
    xyz: [float, float, float]
        X/Y/Z coordinates in Cassini FOV plane.
    M: numpy.array
        FOV rotation matrix.

    Return
    ------
    [float, float, float]
        Longitude and lattitude on the globe.

    """
    x, y, z = np.dot(M, xyz)
    lon = np.degrees(np.arctan2(y, x))
    lat = np.degrees(np.arcsin(z))
    return lon, lat


def footprint(lon, lat, SC_lon, SC_lat, dth=1):
    """Cube ground footprint with limb matching.

    Parameters
    ----------
    lon: numpy.array
        Cube longitude (degE).
    lat: numpy.array
        Cube latitude (degN).
    SC_lon: float
        Sub-spacecraft longitude (degE)
    SC_lat: float
        Sub-spacecraft latitude (degN)
    dth: float
        Limb angular resolution (degree).

    Return
    ------
    [float, float]
        Longitude and latitude footprint coordinates.

    """
    M = R(SC_lon, SC_lat)  # Rotation matrix - Cassini FOV

    # Borders
    t_cond = ~np.isnan(lon[0, :])
    r_cond = ~np.isnan(lon[:, -1])
    b_cond = ~np.isnan(lon[-1, ::-1])
    l_cond = ~np.isnan(lon[::-1, 0])

    top = lonlat2xyz(lon[0, :][t_cond], lat[0, :][t_cond], M)
    right = lonlat2xyz(lon[:, -1][r_cond], lat[:, -1][r_cond], M)
    bottom = lonlat2xyz(lon[-1, ::-1][b_cond], lat[-1, ::-1][b_cond], M)
    left = lonlat2xyz(lon[::-1, 0][l_cond], lat[::-1, 0][l_cond], M)

    xyz = np.array([[], [], []])

    # No edges
    if not (left.any() or top.any() or right.any() or bottom.any()):
        gc = great_circle(SC_lon, SC_lat, npt=int(360/dth + 1))
        return np.hstack([[[gc[0, -1]], [gc[1, -1]]], gc])

    # Top left corner
    if np.isnan(lon[0, 0]) and left.any():
        if left.size > 1:
            l = left
        elif bottom.size > 1:
            l = bottom
        elif right.size > 1:
            l = right
        elif top.size > 1:
            l = top

        if top.size > 1:
            t = top
        elif right.size > 1:
            t = right
        elif bottom.size > 1:
            t = bottom
        elif left.size > 1:
            t = left

        xyz = np.hstack([xyz, corner(l[:, -2], l[:, -1], t[:, 0], t[:, 1], dth=dth)])

    # Top edge
    if top.any():
        xyz = np.hstack([xyz, top])

    # Top right corner
    if np.isnan(lon[0, -1]) and top.any():
        if top.size > 1:
            t = top
        elif left.size > 1:
            t = left
        elif bottom.size > 1:
            t = bottom
        elif right.size > 1:
            t = right

        if right.size > 1:
            r = right
        elif bottom.size > 1:
            r = bottom
        elif left.size > 1:
            r = left
        elif top.size > 1:
            r = top

        xyz = np.hstack([xyz, corner(t[:, -2], t[:, -1], r[:, 0], r[:, 1], dth=dth)])

    # Right edge
    if right.any():
        xyz = np.hstack([xyz, right])

    # Bottom right corner
    if np.isnan(lon[-1, -1]) and right.any():
        if right.size > 1:
            r = right
        elif top.size > 1:
            r = top
        elif left.size > 1:
            r = left
        elif bottom.size > 1:
            r = bottom

        if bottom.size > 1:
            b = bottom
        elif left.size > 1:
            b = left
        elif top.size > 1:
            b = top
        elif right.size > 1:
            b = right

        xyz = np.hstack([xyz, corner(r[:, -2], r[:, -1], b[:, 0], b[:, 1], dth=dth)])

    # Bottom edge
    if bottom.any():
        xyz = np.hstack([xyz, bottom])

    # Bottom left corner
    if np.isnan(lon[-1, 0]) and bottom.any():
        if bottom.size > 1:
            b = bottom
        elif right.size > 1:
            b = right
        elif top.size > 1:
            b = top
        elif left.size > 1:
            b = left

        if left.size > 1:
            l = left
        elif top.size > 1:
            l = top
        elif right.size > 1:
            l = right
        elif bottom.size > 1:
            l = bottom

        xyz = np.hstack([xyz, corner(b[:, -2], b[:, -1], l[:, 0], l[:, 1], dth=dth)])

    # Left edge
    if left.any():
        xyz = np.hstack([xyz, left])

    # Close contour
    xyz = np.hstack([xyz, [[xyz[0, 0]], [xyz[1, 0]], [xyz[2, 0]]]])

    return xyz2lonlat(xyz, M)
