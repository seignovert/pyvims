#!/bin/python

import sys
import numpy as np
from geojson import Polygon, Feature

from .vims import VIMS

LON_WRAP = 90 # Longitude wrapping cutoff

class VIMS_GEOJSON(VIMS):
    def __init__(self,imgID, root=''):
        VIMS.__init__(self, imgID, root)
        return

    def getContour(self):
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

    def getGeoContour(self):
        '''Extract surface Longitude & Latitude'''
        S,L = self.getContour()
        lonlat = []
        for ii in range(len(S)):

            # Wrapping the poles
            if ii > 1:
                deltaLon = self.lon[L[ii],S[ii]] - self.lon[L[ii-1],S[ii-1]]
                meanLat  = .5 * (self.lat[L[ii],S[ii]] + self.lat[L[ii-1],S[ii-1]])

                # Wrap North Pole
                if deltaLon > LON_WRAP:
                    lonlat.append( (-180, meanLat) )
                    lonlat.append( (-180, 90.) )
                    lonlat.append( ( 180, 90.) )
                    lonlat.append( ( 180, meanLat) )

                # Wrap South Pole
                elif deltaLon < -LON_WRAP:
                    lonlat.append( ( 180, meanLat) )
                    lonlat.append( ( 180, -90.) )
                    lonlat.append( (-180, -90.) )
                    lonlat.append( (-180, meanLat) )

            lonlat.append( (float(self.lon[L[ii],S[ii]]), float(self.lat[L[ii],S[ii]])) )
        return lonlat

    def get(self, fout=False):
        '''Get contour geoJSON'''
        lonlat = self.getGeoContour()
        lonlat.append(lonlat[0]) # Last point need to be the same as initial point
        contour = Polygon([lonlat])
        geojson = Feature(geometry=contour, properties=self.properties)
        if fout:
            if fout == '.' or fout == './': fout = ''
            with open(fout+self.imgID+'.geojson', 'w') as f:
                f.write('%s' % geojson)
        return geojson

    @property
    def properties(self):
        '''GeoJSON properties'''
        prop = {}
        prop['imgID'] = self.imgID
        prop['NS']    = self.NS
        prop['NL']    = self.NL
        prop['TIME']  = self.time
        return prop

if __name__ == '__main__':

    imgID = '1743920928_1'
    if len(sys.argv) > 1:
        imgID = sys.argv[1]

    VIMS_GEOJSON(imgID, root='data/').get(save=True)
