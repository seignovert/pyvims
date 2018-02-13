# -*- coding: utf-8 -*-
import os
import numpy as np

from ._communs import getImgID
from .vims_nav import VIMS_NAV
from .spice_geojson import SPICE_GEOJSON

class VIMS_OBJ(object):
    '''VIMS object abstract class'''
    def __init__(self,imgID, root=''):
        self.imgID = getImgID(imgID)
        self.root  = root
        return

    def __repr__(self):
        return "VIMS cube: %s" % self.imgID

    def __str__(self):
        return self.imgID

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        raise NotImplementedError("Subclass must implement abstract method")

    @property
    def readLBL(self):
        '''Read VIMS LBL header'''
        raise NotImplementedError("Subclass must implement abstract method")

    @property
    def readCUB(self):
        '''Read VIMS CUB data file'''
        raise NotImplementedError("Subclass must implement abstract method")

    def setNAV(self):
        try:
            nav = VIMS_NAV(self.imgID, self.root)
            self.lon = nav.lon
            self.lat = nav.lat
        except NameError:
            print "WARNING: NAV file not found"
        return

    def getBand(self, band):
        '''Get band index'''
        if band < self.bands.min():
            raise ValueError('Band too small (Min = %i)' % self.bands.min() )
        if band > self.bands.max():
            raise ValueError('Band too large (Max = %i)' % self.bands.max() )
        return np.argmin(np.abs(self.bands-band))

    def getWvln(self, wvln):
        '''Get neareast wavelength index'''
        if wvln < self.wvlns.min():
            raise ValueError('Wavelength too small (Min = %.3f um)' % self.wvlns.min() )
        if wvln > self.wvlns.max():
            raise ValueError('Wavelength too large (Max = %.3f um)' % self.wvlns.max() )
        return np.argmin(np.abs(self.wvlns-wvln))

    def getIndex(self, band=97, wvln=None):
        '''Get band or wavelength index'''
        if wvln is None:
            return self.getBand(band)
        return self.getWvln(wvln)

    def getImg(self, band=97, wvln=None):
        '''Get image at specific band or wavelength'''
        return self.cube[self.getIndex(band,wvln),:,:]

    def getSpec(self, S=1, L=1):
        '''Get spectra at specific pixel location
        Note:
        -----
            Top-left     pixel = ( 1, 1)
            Top-right    pixel = ( 1,NS)
            Bottom-left  pixel = (NL, 1)
            Bottom-right pixel = (NL,NS)
        '''
        if S < 0:
            raise ValueError('Sample too small (> 0)')
        elif S >= self.NS:
            raise ValueError('Sample too large (< %i)' % self.NS )
        elif L < 0:
            raise ValueError('Line too small (> 0)')
        elif L >= self.NL:
            raise ValueError('Line too large (< %i)' % self.NL )
        return self.cube[:,L-1,S-1]

    def saveJPG(self, band=97, wvln=None, imin=0, imax=None, fout=''):
        '''Save to JPG image file'''
        img  = self.getImg(band,wvln)

        if imax is None: imax = np.nanmax(img)
        data = np.clip( 255.*(img-imin)/(imax-imin),0,255)

        from PIL import Image
        icon = Image.fromarray( np.uint8(data) )
        icon.save( fout+'%s.jpg' % self.imgID )
        return

    def saveGEOJSON(self):
        '''Save field of view into a geojson file'''
        SPICE_GEOJSON(self.target, self.time).save(fout=self.root+self.imgID)
        return
