"""Vertices path module."""

import numpy as np

from matplotlib.path import Path


def path_pole_180(vertices_e, npole=True):
    """Redraw vertices path around the North/South Pole centered on 0.

    Note
    ----
    Vertices must be provided as East longitude [-180°, 180°].

    """
    pole = 90 if npole else -90
    lon_e, lat = np.transpose(vertices_e)
    dist = lon_e[1:] - lon_e[:-1]  # [i + 1] - [i]

    verts = [[lon_e[0], lat[0]]]
    for i in range(len(dist)):
        if abs(dist[i]) > 180:
            if lon_e[i] >= 0:
                f = 1 - (180 - lon_e[i]) / (360 - dist[i])
                f_lon_1, f_lon_2 = 180, -180
            else:
                f = (-180 - lon_e[i]) / dist[i]
                f_lon_1, f_lon_2 = -180, 180

            f_lat = lat[i] + f * (lat[i + 1] - lat[i])

            verts.append([f_lon_1, f_lat])
            verts.append([f_lon_1, pole])
            verts.append([f_lon_2, pole])
            verts.append([f_lon_2, f_lat])

        verts.append([lon_e[i + 1], lat[i + 1]])

    codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) + [Path.CLOSEPOLY]

    return np.array(verts), codes


def path_pole_360(vertices, npole=True):
    """Redraw vertices path around the North/South Pole centered at 180.

    Note
    ----
    Vertices must be provided as West longitude [0°, 360°].

    """
    pole = 90 if npole else -90
    lon, lat = np.transpose(vertices)
    dist = lon[1:] - lon[:-1]  # [i + 1] - [i]

    verts = [[lon[0], lat[0]]]
    for i in range(len(dist)):
        if abs(dist[i]) > 180:
            if lon[i] >= 180:
                f = (360 - lon[i]) / (360 + dist[i])
                f_lon_1, f_lon_2 = 360, 0
            else:
                f = lon[i] / dist[i]
                f_lon_1, f_lon_2 = 0, 360

            f_lat = lat[i] + f * (lat[i + 1] - lat[i])

            verts.append([f_lon_1, f_lat])
            verts.append([f_lon_1, pole])
            verts.append([f_lon_2, pole])
            verts.append([f_lon_2, f_lat])

        verts.append([lon[i + 1], lat[i + 1]])

    codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) + [Path.CLOSEPOLY]

    return np.array(verts), codes


def path_cross_180(vertices_e):
    """Redraw vertices path crossing the change of date meridian (180°).

    Note
    ----
    Vertices must be provided as East longitude [-180°, 180°].

    """
    lon_e, lat = np.transpose(vertices_e)

    # Left polygon
    l_verts = []
    l_lon = lon_e % 360 - 360
    for i in range(len(l_lon) - 1):
        if l_lon[i] < -180 and l_lon[i + 1] < -180:
            continue

        else:
            if l_lon[i] >= -180:
                l_verts.append([lon_e[i], lat[i]])

            if l_lon[i] < -180 or l_lon[i + 1] < -180:
                f = (-180 - l_lon[i]) / (l_lon[i + 1] - l_lon[i])
                f_lat = lat[i] + f * (lat[i + 1] - lat[i])
                l_verts.append([-180, f_lat])

    # Right polygon
    r_verts = []
    r_lon = lon_e % 360
    for i in range(len(r_lon) - 1):
        if r_lon[i] > 180 and r_lon[i + 1] > 180:
            continue

        else:
            if r_lon[i] <= 180:
                r_verts.append([lon_e[i], lat[i]])

            if r_lon[i] > 180 or r_lon[i + 1] > 180:
                f = (180 - r_lon[i]) / (r_lon[i + 1] - r_lon[i])
                f_lat = lat[i] + f * (lat[i + 1] - lat[i])
                r_verts.append([180, f_lat])

    return _merge(l_verts, r_verts)


def path_cross_360(vertices):
    """Redraw vertices path crossing the prime meridian (360°).

    Note
    ----
    Vertices must be provided as West longitude [0°, 360°].

    """
    lon, lat = np.transpose(vertices)

    # Left polygon
    l_verts = []
    l_lon = (lon + 180) % 360 - 180
    for i in range(len(l_lon) - 1):
        if l_lon[i] < 0 and l_lon[i + 1] < 0:
            continue

        else:
            if l_lon[i] >= 0:
                l_verts.append([lon[i], lat[i]])

            if l_lon[i] < 0 or l_lon[i + 1] < 0:
                f = - l_lon[i] / (l_lon[i + 1] - l_lon[i])
                f_lat = lat[i] + f * (lat[i + 1] - lat[i])
                l_verts.append([0, f_lat])

    # Right polygon
    r_verts = []
    r_lon = (lon - 180) % 360 + 180
    for i in range(len(r_lon) - 1):
        if r_lon[i] > 360 and r_lon[i + 1] > 360:
            continue

        else:
            if r_lon[i] <= 360:
                r_verts.append([lon[i], lat[i]])

            if r_lon[i] > 360 or r_lon[i + 1] > 360:
                f = (360 - r_lon[i]) / (r_lon[i + 1] - r_lon[i])
                f_lat = lat[i] + f * (lat[i + 1] - lat[i])
                r_verts.append([360, f_lat])

    return _merge(l_verts, r_verts)


def _merge(lv, rv):
    """Merge left and right vertices."""
    if len(lv) > 2:
        lv.append([lv[0][0], lv[0][1]])
    else:
        raise ValueError(f'Left vertice size invalid: `{len(lv)}`')

    if len(rv) > 2:
        rv.append([rv[0][0], rv[0][1]])
    else:
        raise ValueError(f'Right vertice size invalid: `{len(rv)}`')

    codes = ([Path.MOVETO] + [Path.LINETO] * (len(lv) - 2) + [Path.CLOSEPOLY]
             + [Path.MOVETO] + [Path.LINETO] * (len(rv) - 2) + [Path.CLOSEPOLY])

    return np.vstack([lv, rv]), codes


def area(vertices):
    """Calculate the area of a polygon based on its catesian vertices."""
    x, y = np.transpose(vertices)
    y1 = np.array([*y[1:], y[0]])
    x2 = np.array([*x[2:], *x[:2]])
    return .5 * np.abs(np.sum((x2 - x) * y1))
