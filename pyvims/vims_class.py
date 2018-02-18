# -*- coding: utf-8 -*-
import os
import numpy as np
import cv2
import piexif

from ._communs import getImgID, clipIMG
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
            self.inc = nav.inc
            self.eme = nav.eme
            self.phase = nav.phase
            self.res = nav.res
            self.limb = nav.nan
            self.specular = nav.specular
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

    def getImg(self, band=97, wvln=None):
        '''Get image at specific band or wavelength'''
        return self.cube[self.getIndex(band, wvln), :, :]

    def imgInterp(self, img, imin=0, imax=None, height=256,
                  interp=cv2.INTER_LANCZOS4, equalizer=True):
        '''
        Interpolation:
        - INTER_NEAREST - a nearest-neighbor interpolation
        - INTER_LINEAR - a bilinear interpolation (used by default)
        - INTER_AREA - resampling using pixel area relation.
        - INTER_CUBIC - a bicubic interpolation over 4x4 pixel neighborhood
        - INTER_LANCZOS4 - a Lanczos interpolation over 8x8 pixel neighborhood
        '''
        if img.dtype != 'uint8':
            img = clipIMG(img, imin, imax)

        if not height is None:
            hr = 2 if self.mode[0] == 'HI-RES' else 1
            width = (height * self.NL) / self.NS / hr
            img = cv2.resize(img, (width, height), interpolation=interp)
        
        if equalizer:
            # Create a CLAHE object.
            clahe = cv2.createCLAHE(clipLimit=1, tileGridSize=(2, 2))
            img = clahe.apply(img)
        return img

    def saveJPG(self, img, info='', fout=None, quality=65):
        '''Save to JPG image file'''
        if img.dtype != 'uint8':
            img = clipIMG(img)

        if fout is None:
            fout = self.root
        fname = os.path.join(fout, self.imgID + '.jpg')

        cv2.imwrite(fname, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        cv2.destroyAllWindows()
        self.saveExif(fname, info)

    def saveExif(self, fname, desc=''):
        piexif.insert(
            piexif.dump({
                '0th': {
                    piexif.ImageIFD.Make: u'Cassini Orbiter (NASA)',
                    piexif.ImageIFD.Model: u'Visual and Infrared Mapping Spectrometer(VIMS)',
                    piexif.ImageIFD.ImageNumber: int(self.imgID.split('_')[0]),
                    piexif.ImageIFD.ImageDescription: u'%s - %s %s' % (
                        self.imgID,
                        self.target.title(),
                        desc
                    ),
                    piexif.ImageIFD.DateTime: self.dtime.strftime('%Y:%m:%d %H:%M:%S'),
                    piexif.ImageIFD.XResolution: (self.NS, 1),
                    piexif.ImageIFD.YResolution: (self.NL, 1),
                    piexif.ImageIFD.Copyright: u'NASA/Univ. Arizona/LPG Nantes',
                },
                '1st': {},
                'Exif': {},
                'GPS': {},
                'Interop': {},
                'thumbnail': None
            }
        ), fname)

    @property
    def save_quicklook_0(self):
        '''
        Band: 172
        Wavelength: 2.12 um
        Info: Cloud on 2.03 um wing
        '''
        fout = os.path.join(self.root, 'quicklook_0')
        band = 172
        wvln = self.wvlns[self.getIndex(band)]
        img = self.getImg(band)
        if not os.path.isdir(fout):
            os.mkdir(fout)
        self.saveJPG(self.imgInterp(img), '@ %.2f um [%i]' % (wvln, band), fout)

    def saveGEOJSON(self):
        '''Save field of view into a geojson file'''
        SPICE_GEOJSON(self.target, self.time).save(fout=self.root+self.imgID)
        return
