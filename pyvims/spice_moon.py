#!/bin/python

import numpy as np
import spiceypy as spice

from .spice_cassini import SPICE_CASSINI

def lonlat(pt):
    '''Convert XYZ cartesian corrdinates into R,lon,lat'''
    if isinstance(pt, list):
        r = np.sqrt(np.sum(np.power(pt, 2), 1))
        lon = np.degrees(np.arctan2(pt[:, 1], pt[:, 0]))
        lat = np.degrees(np.arcsin(pt[:, 2] / r))
    else:
        r = np.sqrt(np.sum(np.power(pt, 2)))
        lon = np.degrees(np.arctan2(pt[1], pt[0]))
        lat = np.degrees(np.arcsin(pt[2] / r))
    return r, lon, lat
    
class SPICE_MOON(SPICE_CASSINI):
    def __init__(self, target):
        SPICE_CASSINI.__init__(self)
        self.load()
        self.targ = target.upper()
        self.ref = 'IAU_' + self.targ
        return

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Cassini Spice Kernels tools - Planet/Moon: %s' % str(self)

    def dist(self, utc, abcorr='CN+S' ):
        '''Spacecraft distance'''
        et = spice.str2et(utc)
        pos, _ = spice.spkpos(self.targ, et, self.ref, abcorr, self.obs)
        return lonlat( pos )[0]

    def SC(self, utc, method='INTERCEPT/ELLIPSOID', abcorr='CN+S'):
        '''Sub-spacecraft point'''
        et = spice.str2et(utc)
        pos, _, _ = spice.subpnt(method, self.targ, et,
                              self.ref, abcorr, self.obs)
        return lonlat( pos )

    def SS(self, utc, method='INTERCEPT/ELLIPSOID', abcorr='CN+S'):
        '''Sub-solar point'''
        et = spice.str2et(utc)
        pos, _, _ = spice.subslr(method, self.targ, et,
                              self.ref, abcorr, self.obs)
        return lonlat( pos )

    def CA(self, utc_0, utc_1, step=120, abcorr='CN+S'):
        '''Search Close Approch time and distance'''
        et_0 = spice.str2et(utc_0)
        et_1 = spice.str2et(utc_1)
        times = [x * (et_1-et_0)/step + et_0 for x in range(step)]
        pos, _ = spice.spkpos(self.targ, times, self.ref, abcorr, self.obs)
        dists = np.sqrt(np.sum(np.power(pos, 2), 1))

        # Find the smallest distance
        ca_i = np.argmin(dists)
        ca_et = times[ca_i]
        ca_dist = dists[ca_i]
        return spice.et2utc(ca_et, 'ISOC', 5), ca_dist


class SPICE_TITAN(SPICE_MOON):
    def __init__(self):
        SPICE_MOON.__init__(self, 'TITAN')
        return
