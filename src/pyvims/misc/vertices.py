"""Vertices path module."""

import numpy as np

from matplotlib.path import Path

from .greatcircle import great_circle_arc, great_circle_lat


def _lonlat(path):
    """Extract west longitude, latitude and cross from Path."""
    lon, lat = np.transpose(path.vertices)
    dist = lon[1:] - lon[:-1]  # [i + 1] - [i]
    cross = np.abs(dist) > 180
    return lon, lat, cross


def path_lonlat(path):
    """Redraw path vertices when crossing the pole of the meridian

    Parameters
    ----------
    path: matplotlib.path.Path
        Path to redraw.

    Returns
    -------
    matplotlib.path.Path
        New path in equirectangular projection.

    Raises
    ------
    ValueError
        If the vertice cross more than 2 times the spit meridian.

    """
    lon, lat, cross = _lonlat(path)
    n_cross = np.sum(cross)

    if n_cross == 0:
        return path

    elif n_cross == 1:
        return path_lonlat_pole(lon, lat, cross)

    elif n_cross == 2:
        return path_lonlat_cross(lon, lat)

    raise ValueError('Path vertices cross more than 2 time the split meridian.')


def path_lonlat_pole(lon, lat, cross):
    """Redraw vertices path around the North/South Pole.

    Parameters
    ----------
    lon: list
        Vertice longitude.
    lat: list
        Vertice latitude.
    cross: list
        Is longitude distance is larger than 180°.

    Returns
    -------
    matplotlib.path.Path
        New path in equirectangular projection.

    """
    pole = 90 if lat[np.argmax(np.abs(lat))] >= 0 else -90

    verts = [[lon[0], lat[0]]]
    for i in range(len(cross)):
        if cross[i]:
            _lon = 0 if lon[i] + lon[i + 1] >= 180 else 180

            _lat = great_circle_lat(_lon, lon[i], lat[i],
                                    lon[i + 1], lat[i + 1])

            if lon[i + 1] < lon[i]:
                _lon_1, _lon_2 = (360, 0) if _lon == 0 else (180, -180)
            else:
                _lon_1, _lon_2 = (0, 360) if _lon == 0 else (-180, 180)

            verts.append([_lon_1, _lat])
            verts.append([_lon_1, pole])
            verts.append([_lon_2, pole])
            verts.append([_lon_2, _lat])

        verts.append([lon[i + 1], lat[i + 1]])

    codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) + [Path.CLOSEPOLY]

    return Path(verts, codes)


def path_lonlat_cross(lon, lat):
    """Redraw vertices path crossing the splitted meridian (0° or 180°).

    Parameters
    ----------
    lon: list
        Vertice longitude.
    lat: list
        Vertice latitude.

    Returns
    -------
    matplotlib.path.Path
        New path in equirectangular projection.

    """
    npt = len(lon) - 1
    _lon_l, _lon_r = (0, 360) if np.nanmax(lon) + np.nanmin(lon) >= 180 else (-180, 180)

    # Left polygon
    l_verts = []
    l_lon = (lon + 180 + _lon_l) % 360 - 180 + _lon_l
    for i in range(npt):
        if l_lon[i] < _lon_l and l_lon[i + 1] < _lon_l:
            continue

        else:
            if l_lon[i] >= _lon_l:
                l_verts.append([l_lon[i], lat[i]])

            if l_lon[i] < _lon_l or l_lon[i + 1] < _lon_l:
                _lat = great_circle_lat(_lon_l, l_lon[i], lat[i],
                                        l_lon[i + 1], lat[i + 1])
                l_verts.append([_lon_l, _lat])

    # Right polygon
    r_verts = []
    r_lon = (lon + 180 - _lon_r) % 360 - 180 + _lon_r
    for i in range(npt):
        if r_lon[i] > _lon_r and r_lon[i + 1] > _lon_r:
            continue

        else:
            if r_lon[i] <= _lon_r:
                r_verts.append([lon[i], lat[i]])

            if r_lon[i] > _lon_r or r_lon[i + 1] > _lon_r:
                _lat = great_circle_lat(_lon_r, r_lon[i], lat[i],
                                        r_lon[i + 1], lat[i + 1])
                r_verts.append([_lon_r, _lat])

    return _merge(l_verts, r_verts)


def _merge(lv, rv):
    """Merge left and right vertices to get one path."""
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

    return Path(np.vstack([lv, rv]), codes)


def area(vertices):
    """Calculate the area of a polygon based on its catesian vertices."""
    x, y = np.transpose(vertices)
    y1 = np.array([*y[1:], y[0]])
    x2 = np.array([*x[2:], *x[:2]])
    return .5 * np.abs(np.sum((x2 - x) * y1))


def path_gc_lonlat(path, npt=8):
    """Redraw path using great circle vertices.

    Parameters
    ----------
    path: matplotlib.path.Path
        Path to redraw.
    npt: int, optional
        Number of points in each great circle arc.

    Returns
    -------
    matplotlib.path.Path
        New path in equirectangular projection.

    Raises
    ------
    ValueError
        If the vertice cross more than 2 times the spit meridian.

    """
    lon, lat = path.vertices.T
    nv = len(lon) - 1

    gc = [great_circle_arc(lon[i], lat[i], lon[i + 1], lat[i + 1], npt=npt)
          for i in range(nv)]

    vertices = np.reshape(np.stack(gc, axis=1), (2, nv * npt)).T
    codes = [Path.MOVETO] + [Path.LINETO] * (nv * npt - 2) + [Path.CLOSEPOLY]

    return path_lonlat(Path(vertices, codes))
