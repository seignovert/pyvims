# -*- coding: utf-8 -*-
"""Map plot module."""

import os

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.tri as tri
from mpl_toolkits.basemap import Basemap

from shapely.geometry import Polygon, Point

from .footprint import footprint, great_circle
from ..spice_moon import SPICE_MOON


def triangles_in_coutour(pts, contour):
    """Find triangle inside a contour.

    Parameters
    ----------
    pts: numpy.array
        Input points.
    contour: [[float, …] [float, …]]
        Image footprint.

    Return
    ------
    matplotlib.tri.Triangulation
        Internal tirangles

    """
    tr = tri.Triangulation(*pts)
    poly = Polygon(np.transpose(contour))
    tr.set_mask([not Point(*np.mean(pts[:, t], axis=1)).within(poly)
                 for t in tr.triangles])
    return tr


def map_cube(cube, projection='lonlat', limit=False, lon_0=None, lat_0=None,
             show_cube=True, show_footprint=False, show_pts=True, show_gc=True,
             show_labels=True, bg='Titan_VIMS_ISS', wvln=2.03, fig=None, debug=False):
    """Plot projected cube on a map.

    Parameters
    ----------
    cube: pyvims.VIMS
        Cube to project.
    projection: str, optional
        Projection name. Case sensitive. Avalaible:
            - ``lonlat``: Latitude/Longitude cylindical projection.
            - ``mollweide``: Mollweide projection.
            - ``polar``: Polar projection (North if ``SC lat > 0``, South otherwise).
            - ``ortho``: Cassini fov projection (centered on
                         SC lon/lat if ``lon_0``/``lat_0`` are not provided).
    limit: bool, optional
        Limit FOV on cube corners.
    lon_0: float, optional
        Optional centered longitude for ``ortho`` projection. Set to ``SC lon`` otherwise.
    lat_0: float, optional
        Optional centered lattidue for ``ortho`` or ``polar`` projection.
        Set to ``SC lat`` (for ``ortho``) or ``50ºN/S`` otherwise.
    show_cube: bool, optional
        Show cube data.
    show_footprint: bool, optional
        Show cube footprint.
    show_pts: bool, optional
        Show the SC and SS points locations.
    show_gc: bool, optional
        Show the SC and SS great cricle.
    show_labels: bool, optional
        Show map labels.
    bg: str, optional
        Background frame name.
    wvln: float, optional
        Wavelength to display.
    fig: matplotlib.figure
        Optional matplotlib figure object.
    debug: bool, optional
        Debug mode. Draw cube triangules.

    Raises
    ------
    ValueError
        If the project name is unknown.

    Return
    ------
    mpl_toolkits.basemap.Basemap
        Matplotlib basemap object.

    """

    im = cube.getImg(wvln=wvln)
    moon = SPICE_MOON(cube.target)
    _, SC_lon, SC_lat = moon.SC(cube.time)
    _, SS_lon, SS_lat = moon.SS(cube.time)

    hemi = int(np.sign(SC_lat))

    if fig is None:
        fig = plt.figure(figsize=(12, 12))

    if projection == 'lonlat':
        m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90,
                    llcrnrlon=-180, urcrnrlon=180)

    elif projection == 'mollweide':
        m = Basemap(projection='moll', lon_0=0)

    elif projection == 'polar':
        if SC_lat > 0:
            p = 'npaeqd'
            if lat_0 is None:
                lat_0 = 50
        else:
            p = 'spaeqd'
            if lat_0 is None:
                lat_0 = -50
        m = Basemap(projection=p, boundinglat=lat_0, lon_0=0)

    elif projection == 'ortho':
        if lon_0 is None:
            lon_0 = SC_lon
        if lat_0 is None:
            lat_0 = SC_lat
        m = Basemap(projection='ortho', lat_0=lat_0, lon_0=lon_0)

    else:
        raise ValueError('Projection `%s` unknown.' % projection)

    if bg is not None:
        if bg.upper() == 'TITAN_VIMS_ISS':
            bg = os.path.join(os.path.dirname(__file__), 'bg', 'Titan_VIMS_ISS.jpg')
        elif bg.upper() == 'TITAN_VIMS_ISS-HR':
            bg = os.path.join(os.path.dirname(__file__), 'bg', 'Titan_VIMS_ISS-HR.jpg')
        elif bg.upper() == 'TITAN_ISS':
            bg = os.path.join(os.path.dirname(__file__), 'bg', 'Titan_ISS.jpg')
        elif bg.upper() == 'TITAN_ISS-HR':
            bg = os.path.join(os.path.dirname(__file__), 'bg', 'Titan_ISS-HR.jpg')

        m.warpimage(bg)

    lon = (cube.lon + 180) % 360 - 180
    lat = cube.lat

    f_lon, f_lat = footprint(lon, lat, SC_lon, SC_lat)

    if projection in ['lonlat', 'mollweide']:
        dlon, dlat = 15, 5  # Longitude/latitude overlap
        diff_lon = 270

        # Check if 180º meridan is crossed
        if np.max(f_lon) - np.min(f_lon) > diff_lon:

            lon_p, lat_p = f_lon[-1], f_lat[-1]
            _lon, _lat = np.array([]), np.array([])

            for lon_c, lat_c in zip(f_lon, f_lat):

                if np.abs(lon_c - lon_p) > diff_lon:
                    # North or South pole crossed.

                    if projection == 'lonlat':
                        _lon_p = lon_p + np.sign(lon_p) * dlon
                        _lon_c = lon_c + np.sign(lon_c) * dlon
                        _lat_n = hemi * (90 + dlat)

                        _lon = np.hstack([_lon, [_lon_p, _lon_p, _lon_c, _lon_c]])
                        _lat = np.hstack([_lat, [lat_p, _lat_n, _lat_n, lat_c]])

                    elif projection == 'mollweide':
                        _lat_p = np.arange(lat_p, hemi * 91, hemi * 1)
                        _lat_c = np.arange(lat_c, hemi * 91, hemi * 1)[::-1]

                        _lat_p[np.abs(_lat_p) > 90] = hemi * 90
                        _lat_c[np.abs(_lat_c) > 90] = hemi * 90

                        _lon_p = np.sign(lon_p) * 179 + 0 * _lat_p
                        _lon_c = np.sign(lon_c) * 179 + 0 * _lat_c

                        _lon = np.hstack([_lon, _lon_p, _lon_c])
                        _lat = np.hstack([_lat, _lat_p, _lat_c])

                _lon = np.append(_lon, lon_c)
                _lat = np.append(_lat, lat_c)
                lon_p, lat_p = lon_c, lat_c

            # Replace old by new contour
            f_lon, f_lat = _lon, _lat

            # Duplicate data on the sides
            if projection == 'lonlat':
                limb = np.isnan(lon)
                lon, lat, im = lon[~limb], lat[~limb], im[~limb]

                right_side = lon > (180 - dlon)
                left_side = lon < (-180 + dlon)

                lon = np.hstack([lon, lon[right_side] - 360,  lon[left_side] + 360])
                lat = np.hstack([lat, lat[right_side], lat[left_side]])
                im = np.hstack([im, im[right_side], im[left_side]])

                pole = Point([0, hemi * 90])
                contour = Polygon(np.transpose([f_lon, f_lat]))

                # Add polar pixels
                if pole.within(contour):
                    pole_lon = np.arange(np.min(lon), np.max(lon), dlon)
                    pole_lat = hemi * 91 + 0 * pole_lon
                    pole_im = im[np.argmax(hemi * lat)] + 0 * pole_lon

                    lon = np.append(lon, pole_lon)
                    lat = np.append(lat, pole_lat)
                    im = np.append(im, pole_im)

    contour = m(f_lon, f_lat)

    limb = np.isnan(lon)
    pts = np.array(m(lon[~limb], lat[~limb]))

    if show_cube:
        im = im[~limb]

        # Discard ortho projected pts at 1e30
        if (pts > 1e29).any():
            x, y = pts
            cond = (x < 1e29) & (y < 1e29)
            pts = np.array([x[cond], y[cond]])
            im = im[cond]

        triang = triangles_in_coutour(pts, contour)

        if debug:
            plt.triplot(tri.Triangulation(*pts), color='r')
            plt.triplot(triang)

        plt.tricontourf(triang, im, 255, cmap='gray')

    if show_footprint:
        plt.plot(*contour, 'w-')

    if show_gc:
        SC_gc = np.array(m(*great_circle(SC_lon, SC_lat)))
        SS_gc = np.array(m(*great_circle(SS_lon, SS_lat)))

        # Discard ortho projected pts at 1e30
        SC_gc[SC_gc > 1e29] = np.nan
        SS_gc[SS_gc > 1e29] = np.nan

        plt.plot(*SC_gc, 'b-')
        plt.plot(*SS_gc, '-', color='gold')

    if show_pts:
        SC_pt = m(SC_lon, SC_lat)
        SS_pt = m(SS_lon, SS_lat)

        plt.scatter(*SC_pt, c='b', s=50)
        plt.scatter(*SS_pt, c='gold', s=50)

        if limit:
            xmin, xmax = np.min(pts[0]), np.max(pts[0])
            ymin, ymax = np.min(pts[1]), np.max(pts[1])

        else:
            ax = plt.gca()
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()

        if xmin < SC_pt[0] < xmax and ymin < SC_pt[1] < ymax:
            plt.text(*SC_pt, 'SC\n\n', color='b', va='center', ha='center')

        if xmin < SS_pt[0] < xmax and ymin < SS_pt[1] < ymax:
            plt.text(*SS_pt, 'SS\n\n', color='gold', va='center', ha='center')

    # Define longitudes and latitudes grid
    lons = np.linspace(-180, 180, 19)
    lats = np.linspace(-90, 90, 19)

    # Map labels
    mlabels, plabels = [0, 0, 0, 0], [0, 0, 0, 0]

    if show_labels:
        if projection == 'lonlat':
            mlabels, plabels = [0, 0, 0, 1], [1, 0, 0, 0]
        elif projection == 'mollweide':
            plabels = [1, 0, 0, 0]
        elif projection == 'polar':
            mlabels = [1, 1, 1, 1]

    # Draw meridians and parallels
    m.drawmeridians(lons, linewidth=.25, color='w', labels=mlabels)
    m.drawparallels(lats, linewidth=.25, color='w', labels=plabels)
    m.drawmeridians([0], linewidth=.2, color='r', dashes=[1, 0])
    m.drawparallels([0], linewidth=.2, color='r', dashes=[1, 0])

    if limit:
        xmin, xmax = np.min(pts[0]), np.max(pts[0])
        ymin, ymax = np.min(pts[1]), np.max(pts[1])

        if projection == 'lonlat':
            xmin, xmax = max([xmin, -180]), min([xmax, 180])
            ymin, ymax = max([ymin, -90]), min([ymax, 90])

        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)

    if debug and projection == 'lonlat':
        plt.xlim(-180 - dlon - 5, 180 + dlon + 5)
        plt.ylim(-90 - dlat - 5, 90 + dlat + 5)

    return m
