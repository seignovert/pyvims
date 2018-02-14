#!/bin/python

from .spice_moon import SPICE_MOON
from ._geomerty import BODY_SPHERE

from ._geojson import SS_PT, SC_PT, Shadow_POLYGON, Limb_POLYGON, COLLECTION

class SPICE_GEOJSON(SPICE_MOON):
    def __init__(self, target, time):
        SPICE_MOON.__init__(self, target)
        self.at(time)
        return

    def __repr__(self):
        return 'SPICE GEOJSON tool for %s at %s' % (self.targ, self.utc)

    def at(self, time):
        '''Load spice geometry'''
        self.utc = time if 'T' in time else self.toUTC(time)

        # Load Body, Spacecraft and Sun geometries
        moon_radius, lon_SC, lat_SC = self.SC(self.utc)
        _, lon_SS, lat_SS = self.SS(self.utc)
        dist = self.dist(self.utc)

        self.geoSS = SS_PT(lon_SS, lat_SS)
        self.geoSC = SC_PT(lon_SC, lat_SC)

        # Search projected circles on the moon
        self.body = BODY_SPHERE(moon_radius)

        lonS, latS = self.body.sun(lon_SS, lat_SS)
        self.lonL, self.latL = self.body.limb(dist, lon_SC, lat_SC)

        self.geoShadow = Shadow_POLYGON(lonS, latS)
        self.geoLimb = Limb_POLYGON(self.lonL, self.latL)
        return
    
    def save(self, fout):
        with open(fout+'.geojson', 'w') as f:
                f.write(
                    '%s' % COLLECTION([
                        self.geoShadow, self.geoLimb,
                        self.geoSS, self.geoSC
                    ])
                )

