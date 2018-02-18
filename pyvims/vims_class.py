# -*- coding: utf-8 -*-
import os
import numpy as np
import cv2
import piexif

from ._communs import getImgID, clipIMG, imgInterp
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

    def saveJPG(self, img, info='', fout=None, suffix='', quality=65):
        '''Save to JPG image file'''
        if img.dtype != 'uint8':
            img = clipIMG(img)

        if fout is None:
            fout = self.root
        fname = os.path.join(fout, self.imgID + suffix + '.jpg')

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

    def saveQuicklook(self, name, img, desc):
        '''Save image quicklook'''
        fout = os.path.join(self.root, 'quicklooks')
        if not os.path.isdir(fout):
            os.mkdir(fout)
        self.saveJPG(img, desc, fout, suffix='-'+name)

    def getBands(self, bands):
        '''Get the mean image and wavlength for a list bands'''
        if isinstance(bands, int):
            bands = [bands]
        img = []
        wvln = []
        for band in bands:
            index = self.getBand(band)
            img.append(self.cube[index, :, :])
            wvln.append(self.wvlns[index])
        return np.nanmean(img, axis=0), np.mean(wvln)

    def HR(self, band):
        '''Extract acquisition mode'''
        return self.mode[0] if band > 97 else self.mode[1]  # IR|VIS mode

    def quicklook_Gray(self, name, bands):
        '''Quicklook - Gray image from bands'''
        img, wvln = self.getBands(bands)

        desc = '@ %.2f um [%i' % ( wvln, bands[0])
        if len(bands) > 1:
            desc += '-%i' % bands[-1]
        desc += ']'

        min_band = np.min(bands)
        img = imgInterp(img, hr=self.HR(min_band) )
        self.saveQuicklook('G_'+name, img, desc)

    def quicklook_Ratio(self, name, N, D):
        '''Quicklook - Gray ratio image from bands'''
        img_N, wvln_N = self.getBands(N)
        img_D, wvln_D = self.getBands(D)

        desc = '@ %.2f/%.2f um [%i' % ( wvln_N, wvln_D, N[0])
        if len(N) > 1:
            desc += '-%i' % N[-1]
        desc += '/%i' % D[0]
        if len(D) > 1:
            desc += '-%i' % D[-1]
        desc += ']'

        min_ND = np.min([np.min(N), np.min(D)])
        hr = self.HR(min_ND)
        img_N = imgInterp(img_N, hr=hr, equalizer=False)
        img_D = imgInterp(img_D, hr=hr, equalizer=False)

        img = img_N / img_D
        img[img_D < 1.e-2] = np.nan
        img = imgInterp(img, hr=hr, height=None)

        self.saveQuicklook('R_'+name, img, desc)

    def quicklook_RGB(self, name, R, G, B, eq=True):
        '''
        Quicklook - RGB

        eq: Global RGB channels equalizer on I/F values before binning [0-255]
        '''
        img_R, wvln_R = self.getBands(R)
        img_G, wvln_G = self.getBands(G)
        img_B, wvln_B = self.getBands(B)

        desc = '@ (%.2f, %.2f, %.2f) um [%i-%i, %i-%i, %i-%i]' % (
            wvln_R, wvln_G, wvln_B,
            R[0], R[-1], G[0], G[-1], B[0], B[-1]
        )

        if eq:
            max_RGB = np.max([np.max(img_R), np.max(img_G), np.max(img_B)])
            img_R = clipIMG(img_R, imin=0, imax=max_RGB)
            img_G = clipIMG(img_G, imin=0, imax=max_RGB)
            img_B = clipIMG(img_B, imin=0, imax=max_RGB)
        else:
            img_R = clipIMG(img_R)
            img_G = clipIMG(img_G)
            img_B = clipIMG(img_B)

        img = cv2.merge([img_B, img_G, img_R]) # BGR in cv2

        min_RGB = np.min([np.min(R), np.min(G), np.min(B)])
        img = imgInterp(img, hr=self.HR(min_RGB))

        self.saveQuicklook('RGB_'+name, img, desc)

    @property
    def quicklook_G_203(self):
        '''Quicklook @ 2.03 um [165-169]'''
        name = '203'
        bands = range(165, 169+1)
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_RGB_203_158_279(self):
        '''Quicklook @ (2.03, 1.58, 2.79) um [165-169, 138-141, 212-213]'''
        name = '203_158_279'
        R = range(165, 169+1)
        G = range(138, 141+1)
        B = range(212, 213+1)
        self.quicklook_RGB(name, R, G, B, eq=False)

    @property
    def quicklook_R_159_126(self):
        '''Quicklook @ 1.59/1.26 um [165-169]'''
        name = '159_126'
        N = [139]
        D = [120]
        self.quicklook_Ratio(name, N, D)

    @property
    def quicklook_G_212(self):
        '''Quicklook @ 2.12 um [172]'''
        name = '212'
        bands = [172]
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_RGB_501_158_129(self):
        '''Quicklook @ (5.01, 1.58, 1.29) um [339-351, 138-141, 121-122]'''
        name = '501_158_129'
        R = range(339, 351+1)
        G = range(138, 141+1)
        B = [121, 122]
        self.quicklook_RGB(name, R, G, B, eq=False)

    @property
    def quicklooks(self):
        self.quicklook_G_203
        self.quicklook_RGB_203_158_279
        self.quicklook_R_159_126
        self.quicklook_G_212
        self.quicklook_RGB_501_158_129

    def saveGEOJSON(self):
        '''Save field of view into a geojson file'''
        SPICE_GEOJSON(self.target, self.time).save(fout=self.root+self.imgID)
        return
