# -*- coding: utf-8 -*-
import os
import numpy as np
import cv2
import piexif

from ._communs import getImgID, clipIMG, imgInterp
from .vims_nav import VIMS_NAV
from .vims_nav_isis3 import VIMS_NAV_ISIS3
from .spice_geojson import SPICE_GEOJSON

class VIMS_OBJ(object):
    '''VIMS object abstract class'''
    def __init__(self,imgID, root=''):
        self.imgID = getImgID(imgID)
        self.root  = root
        self.quicklooks_dir = os.path.join(self.root, 'quicklooks')
        self.quicklooks_subdir = None
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
        except NameError:
            try:
                nav = VIMS_NAV_ISIS3(self.imgID, self.root)
            except NameError:
                print("WARNING: NAV file not found")
                return

        self.lon = nav.lon
        self.lat = nav.lat
        self.inc = nav.inc
        self.eme = nav.eme
        self.phase = nav.phase
        self.res = nav.res
        self.limb = nav.nan
        self.specular = nav.specular
        return

    def getBand(self, band):
        '''Get band index'''
        if band < np.nanmin(self.bands):
            raise ValueError('Band too small (Min = %i)' % np.nanmin(self.bands) )
        if band > np.nanmax(self.bands):
            raise ValueError('Band too large (Max = %i)' % np.nanmax(self.bands) )
        return np.nanargmin(np.abs(self.bands-band))

    def getWvln(self, wvln):
        '''Get neareast wavelength index'''
        if wvln < np.nanmin(self.wvlns):
            raise ValueError('Wavelength too small (Min = %.3f um)' % np.nanmin(self.wvlns) )
        if wvln > np.nanmax(self.wvlns):
            raise ValueError('Wavelength too large (Max = %.3f um)' % np.nanmax(self.wvlns) )
        return np.nanargmin(np.abs(self.wvlns-wvln))

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

    def getBands(self, w, dw):
        '''Get the list of bands arounf the wavelength (w ± dw)'''
        with np.errstate(invalid='ignore'):
            return self.bands[np.abs(self.wvlns-w) < dw]

    def getImgBands(self, bands):
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
        return self.mode['VIS'] if band < 97 else self.mode['IR']  # VIS|IR mode

    def jpgQuicklook(self, name, img, desc):
        '''Save image quicklook'''
        fout = self.quicklooks_dir
        if not os.path.isdir(fout):
            os.mkdir(fout)
        fout = os.path.join(fout, name)
        if not os.path.isdir(fout):
            os.mkdir(fout)
        if self.quicklooks_subdir:
            fout = os.path.join(fout, self.quicklooks_subdir)
            if not os.path.isdir(fout):
                os.mkdir(fout)
        self.saveJPG(img, desc, fout)

    def saveJPG(self, img, info='', fout=None, suffix='', quality=65):
        '''Save to JPG image file'''
        if img is None:
            return
        if img.dtype != 'uint8':
            img = clipIMG(img)

        if fout is None:
            fout = self.root
        fname = os.path.join(fout, self.imgID + suffix + '.jpg')

        cv2.imwrite(fname, img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        cv2.destroyAllWindows()
        self.jpgExif(fname, info)

    def jpgExif(self, fname, desc=''):
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

    def quicklook_Gray(self, name, bands):
        '''Quicklook - Gray image from bands'''
        try:
            img, wvln = self.getImgBands(bands)
        except ValueError:
            pass
            print('WARNING: Ratio loading failed for {} -> bands:{}'.format(self.imgID,bands))
            return None

        desc = '@ %.2f um [%i' % ( wvln, bands[0])
        if len(bands) > 1:
            desc += '-%i' % bands[-1]
        desc += ']'

        min_band = np.min(bands)
        img = imgInterp(img, hr=self.HR(min_band) )
        self.jpgQuicklook('G_'+name, img, desc)

    def quicklook_Ratio(self, name, N, D):
        '''Quicklook - Gray ratio image from bands'''
        try:
            img_N, wvln_N = self.getImgBands(N)
            img_D, wvln_D = self.getImgBands(D)
        except ValueError:
            pass
            print('WARNING: Ratio loading failed for {} -> N:{}, D:{}'.format(self.imgID,N,D))
            return None

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

        self.jpgQuicklook('R_'+name, img, desc)

    def quicklook_RGB(self, name, R, G, B, eq=True, R_S=None, G_S=None, B_S=None):
        '''
        Quicklook - RGB

        eq: Global RGB channels equalizer on I/F values before binning [0-255]
        '''
        try:
            img_R, wvln_R = self.getImgBands(R)
            img_G, wvln_G = self.getImgBands(G)
            img_B, wvln_B = self.getImgBands(B)
        except ValueError:
            pass
            print('WARNING: RGB loading failed for {} -> R:{}, G:{}, B:{}'.format(self.imgID,R,G,B))
            return None

        try:
            if R_S:
                img_R_S, wvln_R_S = self.getImgBands(R_S)
                img_R = img_R - .5 * img_R_S
            if G_S:
                img_G_S, wvln_G_S = self.getImgBands(G_S)
                img_G = img_G - .5 * img_G_S
            if B_S:
                img_B_S, wvln_B_S = self.getImgBands(B_S)
                img_B = img_B - .5 * img_B_S
        except ValueError:
            pass
            print('WARNING: RGB substract failed for {} -> R_S:{}, G_S:{}, B_S:{}'.format(self.imgID,R_S,G_S,B_S))
            return None

        desc = '@ (%.2f, %.2f, %.2f) um [%i-%i, %i-%i, %i-%i]' % (
            wvln_R, wvln_G, wvln_B,
            R[0], R[-1], G[0], G[-1], B[0], B[-1]
        )

        if eq:
            over_expo = (img_R < -1.e10) | (img_G < -1.e10) | (img_B < -1.e10)
            max_RGB = np.nanmax([np.nanmax(img_R), np.nanmax(img_G), np.nanmax(img_B)])
            img_R = clipIMG(img_R, imin=0, imax=max_RGB)
            img_G = clipIMG(img_G, imin=0, imax=max_RGB)
            img_B = clipIMG(img_B, imin=0, imax=max_RGB)
            img_R[over_expo] = 255
            img_G[over_expo] = 255
            img_B[over_expo] = 255
        else:
            img_R = clipIMG(img_R)
            img_G = clipIMG(img_G)
            img_B = clipIMG(img_B)

        img = cv2.merge([img_B, img_G, img_R]) # BGR in cv2

        min_RGB = np.min([np.min(R), np.min(G), np.min(B)])
        img = imgInterp(img, hr=self.HR(min_RGB))

        self.jpgQuicklook('RGB_'+name, img, desc)

    def quicklook_RGBR(self, name, R_N, R_D, G_N, G_D, B_N, B_D, eq=True):
        '''
        Quicklook - RGB based on ratios

        eq: Global RGB channels equalizer on I/F values before binning [0-255]
        '''
        try:
            img_R_N, wvln_R_N = self.getImgBands(R_N)
            img_G_N, wvln_G_N = self.getImgBands(G_N)
            img_B_N, wvln_B_N = self.getImgBands(B_N)
            img_R_D, wvln_R_D = self.getImgBands(R_D)
            img_G_D, wvln_G_D = self.getImgBands(G_D)
            img_B_D, wvln_B_D = self.getImgBands(B_D)
        except ValueError:
            pass
            print('WARNING: RGB Ratio loading failed for {} -> R_N:{}, R_D:{}, G_N:{}, G_D:{}, B_N:{}, B_D:{}'.format(
                self.imgID, R_N, R_D, G_N, G_D, B_N, B_D))
            return None


        desc = '@ (%.2f/%.2f, %.2f/%.2f, %.2f/%.2f) um ' % (
            wvln_R_N, wvln_R_D,
            wvln_G_N, wvln_G_D,
            wvln_B_N, wvln_B_D
        )
        desc += '[%i-%i/%i-%i, %i-%i/%i-%i, %i-%i/%i-%i]' % (
            R_N[0], R_N[-1], R_D[0], R_D[-1],
            G_N[0], G_N[-1], G_D[0], G_D[-1],
            B_N[0], B_N[-1], B_D[0], B_D[-1],
        )

        min_RGB_ND = np.min([
            np.min(R_N), np.min(R_D),
            np.min(G_N), np.min(G_D),
            np.min(B_N), np.min(B_D),
        ])
        hr = self.HR(min_RGB_ND)
        img_R_N = imgInterp(img_R_N, hr=hr, equalizer=False)
        img_G_N = imgInterp(img_G_N, hr=hr, equalizer=False)
        img_B_N = imgInterp(img_B_N, hr=hr, equalizer=False)
        img_R_D = imgInterp(img_R_D, hr=hr, equalizer=False)
        img_G_D = imgInterp(img_G_D, hr=hr, equalizer=False)
        img_B_D = imgInterp(img_B_D, hr=hr, equalizer=False)

        img_R = img_R_N / img_R_D
        img_G = img_G_N / img_G_D
        img_B = img_B_N / img_B_D
        img_R[img_R_D < 1.e-2] = np.nan
        img_G[img_G_D < 1.e-2] = np.nan
        img_B[img_B_D < 1.e-2] = np.nan
        
        if eq:
            over_expo = (img_R < -1.e10) | (img_G < -1.e10) | (img_B < -1.e10)
            max_RGB = np.nanmax([np.nanmax(img_R), np.nanmax(img_G), np.nanmax(img_B)])
            img_R = clipIMG(img_R, imin=0, imax=max_RGB)
            img_G = clipIMG(img_G, imin=0, imax=max_RGB)
            img_B = clipIMG(img_B, imin=0, imax=max_RGB)
            img_R[over_expo] = 255
            img_G[over_expo] = 255
            img_B[over_expo] = 255
        else:
            img_R = clipIMG(img_R)
            img_G = clipIMG(img_G)
            img_B = clipIMG(img_B)

        img = cv2.merge([img_B, img_G, img_R])  # BGR in cv2
        img = imgInterp(img, hr=hr, height=None)

        self.jpgQuicklook('RGBR_'+name, img, desc)

    def quicklook_BD(self, name, wvln_L, wvln_C, wvln_R):
        '''Quicklook - Band depth image from bands (center/left/right)'''
        try:
            L = self.bands[self.getIndex(wvln=wvln_L)]
            C = self.bands[self.getIndex(wvln=wvln_C)]
            R = self.bands[self.getIndex(wvln=wvln_R)]
            img_L = self.getImg(wvln=wvln_L)
            img_C = self.getImg(wvln=wvln_C)
            img_R = self.getImg(wvln=wvln_R)
        except ValueError:
            pass
            print(
                'WARNING: Band depth loading failed for {} -> L:{}, C:{}, R:{}'.format(
                    self.imgID, wvln_L, wvln_C, wvln_R))
            return None

        desc = 'BD @ %.2f|%.2f|%.2f um [%i|%i|%i]' % (
            wvln_L, wvln_C, wvln_R, L, C, R)

        hr = self.HR(np.min([L, C, R]))  # == `L` in theory
        img_L = imgInterp(img_L, hr=hr, equalizer=False)
        img_C = imgInterp(img_C, hr=hr, equalizer=False)
        img_R = imgInterp(img_R, hr=hr, equalizer=False)

        l = (wvln_R - wvln_C) / (wvln_R - wvln_L)
        r = (wvln_C - wvln_L) / (wvln_R - wvln_L)
        img = 1. - img_C / (l * img_L + r * img_R)

        img[img < 0] = np.nan
        img[img_L < 1.e-2] = np.nan
        img[img_C < 1.e-2] = np.nan
        img[img_R < 1.e-2] = np.nan

        img = imgInterp(img, hr=hr, height=None)

        self.jpgQuicklook('BD_'+name, img, desc)

    def quicklook_RBD(self, name, wvln_L_N, wvln_C_N, wvln_R_N,
                                  wvln_L_D, wvln_C_D, wvln_R_D):
        '''Quicklook - Ratio of band depth images'''
        try:
            L_N = self.bands[self.getIndex(wvln=wvln_L_N)]
            C_N = self.bands[self.getIndex(wvln=wvln_C_N)]
            R_N = self.bands[self.getIndex(wvln=wvln_R_N)]
            img_L_N = self.getImg(wvln=wvln_L_N)
            img_C_N = self.getImg(wvln=wvln_C_N)
            img_R_N = self.getImg(wvln=wvln_R_N)
        except ValueError:
            pass
            print(
                'WARNING: Band depth loading failed for {} -> L_N:{}, C_N:{}, R_N:{}'.format(
                    self.imgID, wvln_L_N, wvln_C_N, wvln_R_N))
            return None
        try:
            L_D = self.bands[self.getIndex(wvln=wvln_L_D)]
            C_D = self.bands[self.getIndex(wvln=wvln_C_D)]
            R_D = self.bands[self.getIndex(wvln=wvln_R_D)]
            img_L_D = self.getImg(wvln=wvln_L_D)
            img_C_D = self.getImg(wvln=wvln_C_D)
            img_R_D = self.getImg(wvln=wvln_R_D)
        except ValueError:
            pass
            print(
                'WARNING: Band depth loading failed for {} -> L_D:{}, C_D:{}, R_D:{}'.format(
                    self.imgID, wvln_L_D, wvln_C_D, wvln_R_D))
            return None

        desc = 'RBD @ %.2f|%.2f|%.2f um / %.2f|%.2f|%.2f um [%i|%i|%i]/[%i|%i|%i]' % (
            wvln_L_N, wvln_C_N, wvln_R_N, wvln_L_D, wvln_C_D, wvln_R_D, 
            L_N, C_N, R_N, L_D, C_D, R_D)

        hr = self.HR(np.min([L_N, C_N, R_N, L_D, C_D, R_D]))  # == `L` in theory

        img_L_N = imgInterp(img_L_N, hr=hr, equalizer=False)
        img_C_N = imgInterp(img_C_N, hr=hr, equalizer=False)
        img_R_N = imgInterp(img_R_N, hr=hr, equalizer=False)
        img_L_D = imgInterp(img_L_D, hr=hr, equalizer=False)
        img_C_D = imgInterp(img_C_D, hr=hr, equalizer=False)
        img_R_D = imgInterp(img_R_D, hr=hr, equalizer=False)

        l_N = (wvln_R_N - wvln_C_N) / (wvln_R_N - wvln_L_N)
        r_N = (wvln_C_N - wvln_L_N) / (wvln_R_N - wvln_L_N)
        l_D = (wvln_R_D - wvln_C_D) / (wvln_R_D - wvln_L_D)
        r_D = (wvln_C_D - wvln_L_D) / (wvln_R_D - wvln_L_D)

        img_N = 1. - img_C_N / (l_N * img_L_N + r_N * img_R_N)
        img_D = 1. - img_C_D / (l_D * img_L_D + r_D * img_R_D)

        img_N[img_N < 0] = np.nan
        img_N[img_L_N < 1.e-2] = np.nan
        img_N[img_C_N < 1.e-2] = np.nan
        img_N[img_R_N < 1.e-2] = np.nan
        
        img_D[img_D < 0] = np.nan
        img_D[img_L_D < 1.e-2] = np.nan
        img_D[img_C_D < 1.e-2] = np.nan
        img_D[img_R_D < 1.e-2] = np.nan

        img = img_N / img_D
        img[img_D < 1.e-2] = np.nan

        img = imgInterp(img, hr=hr, height=None)

        self.jpgQuicklook('RBD_'+name, img, desc)

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
        B = range(121, 122+1)
        self.quicklook_RGB(name, R, G, B, eq=False)

    @property
    def quicklook_RGBR_158_128_204_128_128_107(self):
        '''Quicklook @ (1.58/1.28, 2.04/1.28, 1.28/1.07) um
        [138-141/120-122, 166-169/120-122, 120-122/108-109]'''
        name = '158_128_204_128_128_107'
        R_N = range(138, 141+1)
        R_D = range(120, 122+1)
        G_N = range(166, 169+1)
        G_D = range(120, 122+1)
        B_N = range(120, 122+1)
        B_D = range(108, 109+1)
        self.quicklook_RGBR(name, R_N, R_D, G_N, G_D, B_N, B_D, eq=False)

    @property
    def quicklook_RGB_501_275_203(self):
        '''Quicklook @ (5.01, 2.75, 2.03) um [339-351, 207-213, 165-169]'''
        name = '501_275_203'
        R = range(339, 351+1)
        G = range(207, 213+1)
        B = range(165, 169+1)
        self.quicklook_RGB(name, R, G, B, eq=False)

    @property
    def quicklook_RGB_231_269_195(self):
        '''Quicklook @ (2.31, 2.69, 1.95) um [153-201, 158-230, 140-171]'''
        name = '231_269_195'
        R = [153, 154, 155, 156, 157, 177, 178, 179, 180, 181,
             182, 183, 184, 185, 186, 187, 188, 189, 190, 191,
             192, 193, 194, 195, 196, 197, 198, 199, 200, 201]
        G = [158, 159, 163, 164, 173, 174, 204, 205, 211, 216, 217, 218,
             219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230]
        B = [140, 141, 165, 166, 167, 168, 169, 170, 171]
        self.quicklook_RGB(name, R, G, B, eq=False)

    @property
    def quicklook_R_203_210(self):
        '''Quicklook @ 2.03/2.10 um [167/171]'''
        name = '203_210'
        N = [167]
        D = [171]
        self.quicklook_Ratio(name, N, D)

    @property
    def quicklook_G_101(self):
        '''Quicklook @ 1.01 um [104-105]'''
        name = '101'
        bands = range(104, 105+1)
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_RGB_277_327_332(self):
        '''Quicklook @ (2.77, 3.27, 3.32) um [211-212, 241-242, 244-244]'''
        name = '277_327_332'
        R = range(211, 212+1)
        G = range(241, 242+1)
        B = [244]
        B_S = [234, 235, 236, 255, 256, 257]
        self.quicklook_RGB(name, R, G, B, eq=False, B_S=B_S)

    @property
    def quicklook_RGB_070_056_045(self):
        '''Quicklook @ (0.70, 0.56, 0.45) um [47-51, 27-31, 12-16]'''
        name = '070_056_045'
        R = range(47, 51+1)
        G = range(27, 31+1)
        B = range(12, 16+1)
        self.quicklook_RGB(name, R, G, B, eq=True)

    @property
    def quicklook_G_501(self):
        '''Quicklook @ 5.01 um [339-351]'''
        name = '501'
        bands = range(339, 351+1)
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_RGB_501_332_322(self):
        '''Quicklook @ (5.01, 3.32, 3.22) um [339-351, 243-245, 238-238]'''
        name = '501_332_322'
        R = range(339, 351+1)
        G = range(243, 245+1)
        G_S = [234, 235, 236, 255, 256, 257]
        B = [238]
        self.quicklook_RGB(name, R, G, B, eq=False, G_S=G_S)

    @property
    def quicklook_G_178(self):
        '''Quicklook @ 1.7877 ± 0.034 um'''
        name = '178'
        bands = self.getBands(1.7877, 0.034)
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_G_17877(self):
        '''Quicklook @ 1.7877 um'''
        name = '17877'
        bands = [self.getIndex(wvln=1.7877)]
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_G_20017(self):
        '''Quicklook @ 2.0017 um'''
        name = '20017'
        bands = [self.getIndex(wvln=2.0017)]
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_G_30969(self):
        '''Quicklook @ 3.0969 um (pic de Fresnel)'''
        name = '30969'
        bands = [self.getIndex(wvln=3.0969)]
        self.quicklook_Gray(name, bands)

    @property
    def quicklook_BD_125(self):
        '''Quicklook @ 1.25 um'''
        name = '125'
        L = 1.1637
        C = 1.2449
        R = 1.377
        self.quicklook_BD(name, L, C, R)

    @property
    def quicklook_BD_150(self):
        '''Quicklook @ 1.50 um'''
        name = '150'
        L = 1.377
        C = 1.5079
        R = 1.804
        self.quicklook_BD(name, L, C, R)

    @property
    def quicklook_BD_165(self):
        '''Quicklook @ 1.65 um'''
        name = '165'
        L = 1.6023
        C = 1.6416
        R = 1.804
        self.quicklook_BD(name, L, C, R)

    @property
    def quicklook_BD_202(self):
        '''Quicklook @ 2.02 um'''
        name = '202'
        L = 1.804
        C = 2.0178
        R = 2.2328
        self.quicklook_BD(name, L, C, R)

    @property
    def quicklook_RBD_150_202(self):
        '''Quicklook @ 1.50 / 2.02 um'''
        name = '150_202'
        L_N = 1.377
        C_N = 1.5079
        R_N = 1.804
        L_D = 1.804
        C_D = 2.0178
        R_D = 2.2328
        self.quicklook_RBD(name, L_N, C_N, R_N, L_D, C_D, R_D)


    def saveQuicklooks(self, dir_out=None, subdir=None):
        if dir_out:
            self.quicklooks_dir = dir_out
        if subdir:
            self.quicklooks_subdir = subdir

        if self.mode['IR'] is not None:
            if self.target.upper() == 'TITAN':
                self.quicklook_G_203
                self.quicklook_RGB_203_158_279
                self.quicklook_R_159_126
                self.quicklook_G_212
                self.quicklook_RGB_501_158_129
                self.quicklook_RGBR_158_128_204_128_128_107
                self.quicklook_RGB_501_275_203
                self.quicklook_RGB_231_269_195
                self.quicklook_R_203_210
                self.quicklook_G_101
                self.quicklook_RGB_277_327_332
                self.quicklook_G_501
                self.quicklook_RGB_501_332_322
            else:
                self.quicklook_G_178
                self.quicklook_G_17877
                self.quicklook_G_20017
                self.quicklook_G_30969

        if self.mode['VIS'] is not None:
            self.quicklook_RGB_070_056_045

    def saveGEOJSON(self, fout=None):
        '''Save field of view into a geojson file'''
        if not fout:
            fout = self.root+self.imgID
        SPICE_GEOJSON(self.target, self.time).save(fout=fout)
        return
