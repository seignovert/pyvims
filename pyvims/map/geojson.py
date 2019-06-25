# -*- coding: utf-8 -*-
"""Export cube as GeoJSON."""

import os

import numpy as np

import geojson

from .footprint import footprint, great_circle
from ..spice_moon import SPICE_MOON


def geo_collection(features):
    """GeoJSON feature collection.

    Properties
    ----------
    features: float
        GeoJSON features.

    Return
    ------
    geojson.FeatureCollection
        GeoJSON collection of features.

    """
    return geojson.FeatureCollection(features=features)


def geo_pt(lon, lat, name=None, desc=None, color=None, radius=10, alpha=1):
    """GeoJSON Point-circle based on LineString feature.

    Properties
    ----------
    lon: float
        Point longitude (degE).
    lat: float
        Point latitude (degN).
    name: str, optional
        Point name.
    desc: str, optional
        Point description.
    color: str, optional
        Point color.
    radius: int, optional
        Point radius.
    alpha: float, optional
        Point opacity.

    Return
    ------
    geojson.Feature
        GeoJSON point.

    """
    prop = {
        'stroke-width': radius,
        'stroke-opacity': alpha,
    }
    if name:
        prop['id'] = name
    if desc:
        prop['desc'] = desc
    if color:
        prop['stroke'] = color

    return geojson.Feature(
        geometry=geojson.LineString([(lon, lat), (lon, lat)]),
        properties=prop
    )


def geo_polygon(lons, lats, name=None, desc=None, color=None, alpha=.25):
    """GeoJSON polygon.

    Properties
    ----------
    lons: [float]
        Polygon longitudes (degE).
    lats: [float]
        Polygon latitudes (degN).
    name: str, optional
        Polygon name.
    desc: str, optional
        Polygon description.
    color: str, optional
        Polygon color.
    alpha: float, optional
        Polygon opacity.

    Return
    ------
    geojson.Feature
        GeoJSON polygon.

    """
    prop = {
        'stroke-width': 0,
        'fill-opacity': alpha
    }
    if name:
        prop['id'] = name
    if desc:
        prop['desc'] = desc
    if color:
        prop['fill'] = color

    return geojson.Feature(
        geometry=geojson.Polygon([[(lon, lat) for lon, lat in zip(lons, lats)]]),
        properties=prop
    )


def ss_pt(lon, lat):
    """Sub-solar point.

    Properties
    ----------
    lon: float
        Point SS longitude (degE).
    lat: float
        Point SS latitude (degN).

    Return
    ------
    geojson.Feature
        GeoJSON SS point.

    """
    return geo_pt(lon, lat, 'SS', 'Sub-solar point', 'yellow')


def sc_pt(lon, lat):
    """Sub-spacecraft point.

    Properties
    ----------
    lon: float
        Point SC longitude (degE).
    lat: float
        Point SC latitude (degN).

    Return
    ------
    geojson.Feature
        GeoJSON SC point.

    """
    return geo_pt(lon, lat, 'SC', 'Sub-spacecraft point', 'blue')


def night_gc(lons, lats):
    """Night great circle.

    Properties
    ----------
    lons: [float]
        Night side longitudes (degE).
    lats: [float]
        Night side latitudes (degN).

    Return
    ------
    geojson.Feature
        GeoJSON night polygon.

    """
    return geo_polygon(lons, lats, 'Shadow', 'Casted shadow on the planet', 'black', .5)


def fov_gc(lons, lats):
    """Field of view great circle.

    Properties
    ----------
    lons: [float]
        Field of view longitudes (degE).
    lats: [float]
        Field of view latitudes (degN).

    Return
    ------
    geojson.Feature
        GeoJSON field of view polygon.

    """
    return geo_polygon(lons, lats, 'Limb', 'Limb field of view', 'blue')


def footprint_poly(lons, lats):
    """Footprint polygon.

    Properties
    ----------
    lons: [float]
        Footprtint longitudes (degE).
    lats: [float]
        Footprtint latitudes (degN).

    Return
    ------
    geojson.Feature
        GeoJSON footprtint polygon.

    """
    return geo_polygon(lons, lats, 'Footprint', 'Projected cube footprint', 'red')


def geojson_cube(cube, save=False, root=''):
    """Create GeoJson object.

    Paramaters
    ----------
    cube: pyvims.VIMS
        VIMS cube
    save: bool, optional
        Save geojson into a file.
    root: str, optional
        Root location where the file will be saved.

    Return
    ------
    geojson.FeatureCollection
        GeoJSON collection of features.

    """
    moon = SPICE_MOON(cube.target)
    _, SC_lon, SC_lat = moon.SC(cube.time)
    _, SS_lon, SS_lat = moon.SS(cube.time)

    # SC/SS pts
    sc = sc_pt(SC_lon, SC_lat)
    ss = ss_pt(SS_lon, SS_lat)

    # FOV apparent radius
    ra = np.sqrt(1 - (moon.radius / moon.dist(cube.time))**2)

    # Great circles
    night = night_gc(*great_circle(SC_lon, SC_lat, ra=ra))
    fov = fov_gc(*great_circle(SS_lon, SS_lat))

    # Footprint
    proj = footprint_poly(*footprint(cube.lon, cube.lat, SC_lon, SC_lat, ra=ra))

    collection = geo_collection([night, fov, proj, ss, sc])

    if save:
        with open(os.path.join(root, '%s.geojson' % cube.imgID), 'w') as f:
            f.write('%s' % collection)
        return None

    return collection
