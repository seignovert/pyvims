# -*- coding: utf-8 -*-
import geojson

LON_WRAP = 90  # Longitude wrapping cutoff


def PT(lon, lat, id=None, desc=None, color=None, radius=10, alpha=1):
    '''Point/Circle based on LineString feature'''
    prop = {
        'stroke-width': radius,
        'stroke-opacity': alpha,
    }
    if id:
        prop['id'] = id
    if desc:
        prop['desc'] = desc
    if color:
        prop['stroke'] = color

    return geojson.Feature(
        geometry=geojson.LineString([(lon, lat), (lon, lat)]),
        properties=prop
    )

def SS_PT(lon, lat):
    '''Sub-solar point'''
    return PT(lon, lat, 'SS', 'Sub-solar point', 'yellow')

def SC_PT(lon, lat):
    '''Sub-spacecraft point'''
    return PT(lon, lat, 'SC', 'Sub-spacecraft point', 'blue')


def POLYGON(lons, lats):
    '''
        Create GeoJson Polygon from lons/lats arrays
        with polar wrapping around the poles if the
        longitude cross the change of day meridian.
    '''
    lonlat = []
    for ii in range(len(lons)):
        # Wrapping the poles
        if ii > 1:
            deltaLon = lons[ii] - lons[ii-1]
            meanLat = .5 * (lats[ii] + lats[ii-1])

            # Wrap North Pole
            if deltaLon > LON_WRAP:
                lonlat.append((-180, meanLat))
                lonlat.append((-180, 90.))
                lonlat.append((180, 90.))
                lonlat.append((180, meanLat))

            # Wrap South Pole
            elif deltaLon < -LON_WRAP:
                lonlat.append((180, meanLat))
                lonlat.append((180, -90.))
                lonlat.append((-180, -90.))
                lonlat.append((-180, meanLat))

        lonlat.append((float(lons[ii]), float(lats[ii])))

    return geojson.Polygon([lonlat])

def fillPOLYGON(lons, lats, id=None, desc=None, color=None, alpha=.25):
    '''GeoJson polygone with properties'''
    prop = {
        'stroke-width': 0,
        'fill-opacity': alpha
    }
    if id:
        prop['id'] = id
    if desc:
        prop['desc'] = desc
    if color:
        prop['fill'] = color

    return geojson.Feature(
        geometry=POLYGON(lons, lats),
        properties=prop
    )

def Shadow_POLYGON(lons, lats):
    '''Casted shadow on the planet'''
    return fillPOLYGON(lons[::-1], lats[::-1], 'Shadow',
                       'Casted shadow on the planet', 'black', .5)

def Limb_POLYGON(lons, lats):
    '''Casted shadow on the planet'''
    return fillPOLYGON(lons, lats, 'Limb', 'Limb field of view', 'blue')


def COLLECTION(features):
    '''GeoJson feature collection'''
    return geojson.FeatureCollection( features=features )

    
