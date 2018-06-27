# -*- coding: utf-8 -*-
import numpy as np
from osgeo import osr


def srs(lat_0, lon_0, R, target_name):
    '''Spatial Reference for sub-spacecraft orthographic projection.
    Centered at (`lat`, `lon`) on a sphere of radius `R` (km).'''
    srs = osr.SpatialReference()
    wkt = 'PROJCS["{} sub-spacecraft orthographic projection",'.format(target_name.title()) + \
          'GEOGCS["GCS_Sphere",' + \
          'DATUM["{}_SPHERE",'.format(target_name.upper()) + \
          'SPHEROID["SPHERE",{},0]],'.format(1.e3*R) + \
          'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],' + \
          'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],' + \
          'PROJECTION["Orthographic"],' + \
          'PARAMETER["latitude_of_origin",{}],'.format(lat_0) + \
          'PARAMETER["central_meridian",{}],'.format(lon_0 % 360) + \
          'PARAMETER["false_easting",0],' + \
          'PARAMETER["false_northing",0],' + \
          'UNIT["Meter",1,AUTHORITY["EPSG","9001"]]]'
    srs.ImportFromWkt(wkt)
    return srs

def xy(lat, lon, lat_0=0, lon_0=0, R=1.e-3):
    '''(X,Y) coordinates for orthographic projection centered on
    (`lat_0`, `lon_0`) on a sphere of radius radius `R` (km)'''
    phi = np.radians(lat)
    lambd = np.radians(lon)
    phi_0 = np.radians(lat_0)
    lambda_0 = np.radians(lon_0)
    x = 1.e3 * R * np.cos(phi) * np.sin(lambd - lambda_0)
    y = 1.e3 * R * (np.cos(phi_0) * np.sin(phi) - np.sin(phi_0)
                  * np.cos(phi) * np.cos(lambd - lambda_0))
    cos_c = np.sin(phi_0) * np.sin(phi) + np.cos(phi_0) * \
            np.cos(phi) * np.cos(lambd - lambda_0)
    clip = cos_c < 0
    x[clip] = np.nan
    y[clip] = np.nan
    return x, y

def grid(lat, lon, lat_0, lon_0, R, npt):
    '''Init interpolation grid'''
    x, y = xy(lat, lon, lat_0, lon_0, R)
    xmin, ymin = [np.nanmin(x), np.nanmin(y)]
    xmax, ymax = [np.nanmax(x), np.nanmax(y)]
    Y, X = np.mgrid[ymax:ymin:npt * 1j, xmin:xmax:npt * 1j]

    xres = (xmax - xmin) / float(npt)
    yres = (ymax - ymin) / float(npt)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)

    return x, y, X, Y, geotransform
