#!/bin/python

import sys
import numpy as np
from ._geojson import fillPOLYGON

from .vims_nav import VIMS_NAV

LON_WRAP = 90 # Longitude wrapping cutoff

class VIMS_NAV_GEOJSON(VIMS_NAV):
    def __init__(self,imgID, root=''):
        VIMS_NAV.__init__(self, imgID, root)
        return

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
                           'red')

    @property
    def save(self):
        with open(self.root+self.imgID+'.geojson', 'w') as f:
                f.write('%s' % self.contour)

if __name__ == '__main__':

    imgID = '1743920928_1'
    if len(sys.argv) > 1:
        imgID = sys.argv[1]

    VIMS_GEOJSON(imgID, root='data/').get(fout='.')
