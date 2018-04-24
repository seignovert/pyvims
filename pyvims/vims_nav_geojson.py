#!/bin/python

import sys
import numpy as np
from ._geojson import fillPOLYGON, COLLECTION

from .vims_nav import VIMS_NAV
from .spice_geojson import SPICE_GEOJSON

def border(nan):
    '''Extract Left/Middle/Right borders on a NaN line'''
    left = None
    right = None
    for i in range(len(nan)):
        if not nan[i]:
            right = i
            if left is None:
                left = i
    middle = None if left is None else (left + right)/2
    if middle == left or middle == right:
        left, middle, right = (None, None, None)
    return left, middle, right

def limbPts(lons, lats, A, B):
    '''
    Extract longitudes/latitudes on the limb between points A and B
    '''
    i = np.argmin((lons - A[0])**2 + (lats - A[1])**2)
    j = np.argmin((lons - B[0])**2 + (lats - B[1])**2)

    lon = []
    lat = []
    if i < j:
        for k in np.arange(i, j+1):
            lon.append(lons[k])
            lat.append(lats[k])
    else:
        for k in np.arange(i, len(lons)):
            lon.append(lons[k])
            lat.append(lats[k])
        for k in np.arange(0, j+1):
            lon.append(lons[k])
            lat.append(lats[k])
    return lon, lat

def borderPts(lons, lats, pts):
    '''
    Extract longitudes/latitudes on a arc between points A, B and C
    '''
    npt = len(lons)
    A, B, C = pts
    i = np.argmin((lons - A[0])**2 + (lats - A[1])**2)
    m = np.argmin((lons - B[0])**2 + (lats - B[1])**2)
    j = np.argmin((lons - C[0])**2 + (lats - C[1])**2)

    # Check arc orientation
    mm = m if i >= m else m - npt
    jj = j if i >= j else j - npt
    if mm < jj:
        lons = lons[::-1]
        lats = lats[::-1]
        i = np.argmin((lons - A[0])**2 + (lats - A[1])**2)
        j = np.argmin((lons - C[0])**2 + (lats - C[1])**2)

    # Ajust the range to remove the inital point if necessary
    if i != npt-1:
        sig = np.sign( (lons[i] - lons[i+1])*(lons[i] - A[0]) )
    else:
        sig = np.sign( (lons[i] - lons[0])*(lons[i] - A[0]) )
    if sig < 0:
        i -= 1

    # Ajust the range to remove the last point if necessary
    if j != 0:
        sig = np.sign((lons[j] - lons[j-1])*(lons[j] - C[0]))
    else:
        sig = np.sign((lons[j] - lons[-1])*(lons[j] - C[0]))
    if sig < 0:
        j += 1

    # Fill lon/lat list
    lon = [A[0]]
    lat = [A[1]]
    if i > j:
        for k in np.arange(i, j-1, -1):
            lon.append(lons[k])
            lat.append(lats[k])
    else:
        for k in np.arange(i, 0-1, -1):
            lon.append(lons[k])
            lat.append(lats[k])
        for k in np.arange(npt-1, j-1, -1):
            lon.append(lons[k])
            lat.append(lats[k])
    lon.append(C[0])
    lat.append(C[1])
    return lon, lat


class VIMS_NAV_GEOJSON(VIMS_NAV, SPICE_GEOJSON):
    def __init__(self,imgID, root=''):
        VIMS_NAV.__init__(self, imgID, root)
        SPICE_GEOJSON.__init__(self, self.target, self.time)
        return

    @property
    def borders(self):
        '''Extract surface contour'''
        # Top border
        l, m, r = border(self.nan[0, :])
        top = None if m is None else [
            [self.lon[0, l], self.lat[0, l]],
            [self.lon[0, m], self.lat[0, m]],
            [self.lon[0, r], self.lat[0, r]]
        ]

        # Right border
        t, m, b = border(self.nan[:, self.NS-1])
        right = None if m is None else [
            [self.lon[t, self.NS-1], self.lat[t, self.NS-1]],
            [self.lon[m, self.NS-1], self.lat[m, self.NS-1]],
            [self.lon[b, self.NS-1], self.lat[b, self.NS-1]]
        ]

        # Bottom border
        l, m, r = border(self.nan[self.NL-1, :])
        bottom = None if m is None else [
            [self.lon[self.NL-1, r], self.lat[self.NL-1, r]],
            [self.lon[self.NL-1, m], self.lat[self.NL-1, m]],
            [self.lon[self.NL-1, l], self.lat[self.NL-1, l]]
        ]

        # left border
        t, m, b = border(self.nan[:, 0])
        left = None if m is None else [
            [self.lon[b, 0], self.lat[b, 0]],
            [self.lon[m, 0], self.lat[m, 0]],
            [self.lon[t, 0], self.lat[t, 0]]
        ]
        return top, right, bottom, left

    @property
    def footprint(self):
        '''Intersection between the limb and ground circles'''
        top, right, bottom, left = self.borders

        if (top, right, bottom, left) == (None, None, None, None):
            # No borders on the limb
            lons = self.lonL
            lats = self.latL
        else:
            lons = []
            lats = []

            if top:
                # Top border
                lonT, latT = self.body.ground(top)
                lon, lat = borderPts(lonT, latT, top)
                lons.extend(lon)
                lats.extend(lat)

                if right:
                    if top[2] == right[0]:
                        # Same corner
                        lon = [top[2][0]]
                        lat = [top[2][1]]
                    else:
                        # Top-Right limb
                        lon, lat = limbPts(
                            self.lonL, self.latL, top[2], right[0])
                elif bottom:
                    # Right limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, top[2], bottom[0])
                elif left:
                    # Right-Bottom limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, top[2], left[0])
                else:
                    # Right-Bottom-Left limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, top[2], top[0])
                lons.extend(lon)
                lats.extend(lat)

            if right:
                # Right border
                lonR, latR = self.body.ground(right)
                lon, lat = borderPts(lonR, latR, right)
                lons.extend(lon)
                lats.extend(lat)

                if bottom:
                    if right[2] == bottom[0]:
                        # Same corner
                        lon = [right[2][0]]
                        lat = [right[2][1]]
                    else:
                        # Bottom-Right limb
                        lon, lat = limbPts(
                            self.lonL, self.latL, right[2], bottom[0])
                elif left:
                    # Bottom limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, right[2], left[0])
                elif top:
                    # Bottom-Left limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, right[2], top[0])
                else:
                    # Bottom-Left-Top limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, right[2], right[0])
                lons.extend(lon)
                lats.extend(lat)

            if bottom:
                # Bottom border
                lonB, latB = self.body.ground(bottom)
                lon, lat = borderPts(lonB, latB, bottom)
                lons.extend(lon)
                lats.extend(lat)

                if left:
                    if bottom[2] == left[0]:
                        # Same corner
                        lon = [bottom[2][0]]
                        lat = [bottom[2][1]]
                    else:
                        # Bottom-left limb
                        lon, lat = limbPts(
                            self.lonL, self.latL, bottom[2], left[0])
                elif top:
                    # Left limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, bottom[2], top[0])
                elif right:
                    # Left-Top limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, bottom[2], right[0])
                else:
                    # Left-Top-Right limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, bottom[2], bottom[0])
                lons.extend(lon)
                lats.extend(lat)

            if left:
                # Left border
                lonL, latL = self.body.ground(left)
                lon, lat = borderPts(lonL, latL, left)
                lons.extend(lon)
                lats.extend(lat)

                if top:
                    if left[2] == top[0]:
                        # Same corner
                        lon = [left[2][0]]
                        lat = [left[2][1]]
                    else:
                        # Top-left limb
                        lon, lat = limbPts(
                            self.lonL, self.latL, left[2], top[0])
                elif right:
                    # Top limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, left[2], right[0])
                elif bottom:
                    # Top-Right limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, left[2], bottom[0])
                else:
                    # Top-Right-Bottom limb
                    lon, lat = limbPts(
                        self.lonL, self.latL, left[2], left[0])
                lons.extend(lon)
                lats.extend(lat)

        return fillPOLYGON(lons, lats, 'fp_%s' % self.imgID,
                           'Cube: %s -- Footprint' % self.imgID,
                           'red')

    @property
    def contourSL(self):
        '''Extract surface contour'''
        cntr_S = [] ; cntr_L = []
        for s in range(self.NS):
            for l in range(self.NL):
                if not self.nan[l,s]:
                    cntr_S.append(s)
                    cntr_L.append(l)
                    break

        S = cntr_S[-1]; L = cntr_L[-1]
        for l in range(L+1, self.NL):
            if self.nan[l,s]:
                break
            cntr_S.append(S)
            cntr_L.append(l)

        for s in np.flip(range(S),0):
            for l in np.flip(range(self.NL),0):
                if not self.nan[l,s]:
                    cntr_S.append(s)
                    cntr_L.append(l)
                    break

        S = cntr_S[-1]; L = cntr_L[-1]
        for l in np.flip(range(cntr_L[0]+1, L),0):
            if self.nan[l,s]:
                break
            cntr_S.append(S)
            cntr_L.append(l)

        return cntr_S, cntr_L

    @property
    def contour(self):
        '''Get contour geoJSON'''
        S, L = self.contourSL
        lons = []
        lats = []
        for ii in range(len(S)):
            lons.append(self.lon[L[ii], S[ii]])
            lats.append(self.lat[L[ii], S[ii]])

        return fillPOLYGON(lons, lats, 'cntr_%s' % self.imgID,
                           'Cube: %s -- NAV contours' % self.imgID,
                           'magenta', .1)

    def save(self, verbose=True, fout=None):
        root = self.root if fout is None else fout
        fname = root + self.imgID + '.geojson'
        with open(fname, 'w') as f:
                f.write(
                    '%s' % COLLECTION([
                        self.geoShadow,
                        self.geoLimb,
                        self.contour,
                        self.footprint,
                        self.geoSS,
                        self.geoSC
                    ])
                )
        if verbose:
            print("GeoJSON created: %s" % fname)
