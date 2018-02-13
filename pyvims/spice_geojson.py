#!/bin/python

from .spice_moon import SPICE_MOON
from ._communs import BODY_SPHERE

from ._geojson import SS_PT, SC_PT, Shadow_POLYGON, Limb_POLYGON, GEOJSON

class SPICE_GEOJSON(SPICE_MOON):
    def __init__(self, target, time=None):
        SPICE_MOON.__init__(self, target)
        self.geojson = None
        if time:
            self.loadGeometry(time)
        return

    def __repr__(self):
        return 'SPICE GEOJSON tool for %s at %s' % (self.targ, self.utc)

    def loadGeometry(self, time):
        '''Load spice geometry'''
        self.utc = time if 'T' in time else self.toUTC(time)

        # Load Body, Spacecraft and Sun geometries
        moon_radius, lon_SC, lat_SC = self.SC(self.utc)
        _, lon_SS, lat_SS = self.SS(self.utc)
        dist = self.dist(self.utc)

        SS = SS_PT(lon_SS, lat_SS)
        SC = SC_PT(lon_SC, lat_SC)

        # Search projected circles on the moon
        moon = BODY_SPHERE(moon_radius)

        lonS, latS = moon.sun(lon_SS, lat_SS)
        lonL, latL = moon.limb(dist, lon_SC, lat_SC)

        Shadow = Shadow_POLYGON(lonS, latS)
        Limb = Limb_POLYGON(lonL, latL)

        self.geojson = GEOJSON([Shadow, Limb, SS, SC])
        return
    
    def save(self, fout):
        with open(fout+'.geojson', 'w') as f:
                f.write('%s' % self.geojson)

