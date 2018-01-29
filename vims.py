#!/bin/python

import sys, os
import numpy as np
import pvl
from datetime import datetime as dt
from geojson import Polygon, Feature

NaN = -99999.
LON_WRAP = 90 # Longitude wrapping cutoff

class VIMS:
    def __init__(self,imgID):
        self.imgID = imgID
        self.load()
        return

    def __str__(self):
        return self.imgID

    def __repr__(self):
        return "VIMS cube: %s" % self

    @property
    def cub(self):
        '''Check if CUB file exists.'''
        cub_file = 'CM_' + self.imgID + '.cub'
        if not os.path.isfile(cub_file):
            raise ValueError('The cube file was not found')
        return cub_file

    @property
    def nav(self):
        '''Check if NAV file exists.'''
        nav_file = 'V' + self.imgID + '.nav'
        if not os.path.isfile(nav_file):
            raise ValueError('The navigation file was not found')
        return nav_file

    def load(self):
        self.readLBL()
        self.readCUB()
        self.readNAV()
        return

    def readLBL(self):
        self.lbl = pvl.load(self.cub)
        for ii, axis in enumerate(self.lbl['QUBE']['AXIS_NAME']):
            if axis == 'SAMPLE':
                self.NS = int(self.lbl['QUBE']['CORE_ITEMS'][ii])
            elif axis == 'LINE':
                self.NL = int(self.lbl['QUBE']['CORE_ITEMS'][ii])
            elif axis == 'BAND':
                self.NB = int(self.lbl['QUBE']['CORE_ITEMS'][ii])

        self.obs    = self.lbl['QUBE']['INSTRUMENT_HOST_NAME']
        self.inst   = self.lbl['QUBE']['INSTRUMENT_ID']
        self.target = self.lbl['QUBE']['TARGET_NAME']
        self.expo   = self.lbl['QUBE']['EXPOSURE_DURATION']
        self.start  = self.lbl['QUBE']['START_TIME']
        self.stop   = self.lbl['QUBE']['STOP_TIME']
        self.dtime  = (self.stop - self.start)/2 + self.start
        self.time   = self.dtime.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.year   = self.dtime.year
        self.doy    = int(self.dtime.strftime('%j'))
        self.year_d = self.year + (self.doy-1)/365. # Decimal year [ISSUE: doest not apply take into account bissextile years]
        self.date   = self.dtime.strftime('%Y/%m/%d')

        self.wvlns = np.array(self.lbl['QUBE']['BAND_BIN']['BAND_BIN_CENTER'])
        self.bands = np.array(self.lbl['QUBE']['BAND_BIN']['BAND_BIN_ORIGINAL_BAND'])
        return

    def readCUB(self):
        '''Read VIMS CUB file'''
        IDFoffset, nbytes, dtype = self.getType()
        cube = np.zeros((self.NB, self.NL, self.NS))

        with open(self.cub) as f:
            f.seek(IDFoffset, os.SEEK_SET) # Skip Ascii header

            if self.lbl['QUBE']['AXIS_NAME'] == ['SAMPLE', 'BAND', 'LINE']:
                for line in range(self.NL):
                    for band in range(self.NB):
                        sample = np.frombuffer(f.read(nbytes),dtype=dtype) # Read image sample
                        cube[band, line, :] = sample
            elif self.lbl['QUBE']['AXIS_NAME'] == ['SAMPLE', 'LINE', 'BAND']:
                for band in range(self.NB):
                    for line in range(self.NL):
                        sample = np.frombuffer(f.read(nbytes),dtype=dtype) # Read image sample
                        cube[band, line, :] = sample
            else:
                raise TypeError('AXIS_NAME unknown')
                return None
        self.cube = cube
        return

    def readNAV(self):
        '''Read VIMS NAV file'''
        with open(self.nav) as f:
            lbl = {}; IDFoffset = 0
            for line in f.readlines():
                IDFoffset += len(line)
                if line == 'END\r\n' or line == 'FIN\r\n' or line == 'FIN\n':
                    break
                elif '.ker' in line:
                    self.flyby = int(line.rstrip('\r\n')[-8:-5])

        # Read binary file
        _, nbytes, dtype = self.getType()
        nbytes *= self.NL
        shape = (self.NL, self.NS)

        with open(self.nav, 'rb') as f:
            f.seek(IDFoffset+2, os.SEEK_SET) # Skip Ascii header
            self.lon = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) #% 360 # Pixel central longitude [East]
            self.lat = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) # Pixel central latitude [North]

        self.lon.setflags(write=1)
        self.lat.setflags(write=1)

        self.nan = (self.lon == NaN)
        self.lon[self.nan] = np.nan
        self.lat[self.nan] = np.nan
        return None

    def getType(self):
        if self.lbl['QUBE']['CORE_ITEM_TYPE'] == 'SUN_INTEGER':
            arch = '>' # Big endian
        else:
            arch = '<' # Little endian

        if int(self.lbl['QUBE']['CORE_ITEM_BYTES']) == 2:
            byte = 'i'
        elif int(self.lbl['QUBE']['CORE_ITEM_BYTES']) == 4:
            byte = 'f'
        else:
            raise ValueError('Unknown CORE_ITEM_BYTES')

        dtype = np.dtype(arch+byte)

        IDFoffset = (int(self.lbl['^QUBE']) - 1) * int(self.lbl['RECORD_BYTES'])
        nbytes = self.NS * int(self.lbl['QUBE']['CORE_ITEM_BYTES'])
        return IDFoffset, nbytes, dtype

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
        return self.data[:,L-1,S-1]

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

    def lonlat(self):
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

    def geoJSON(self, save=False):
        '''Get contour geoJSON'''
        lonlat = self.lonlat()
        lonlat.append(lonlat[0]) # Last point need to be the same as initial point
        contour = Polygon([lonlat])
        geojson = Feature(geometry=contour, properties=self.properties)
        if save:
            with open('geojson/'+self.imgID+'.geojson', 'w') as f:
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

    def saveJPG(self, band=97, wvln=None, imin=0, imax=None):
        '''Save to JPG image file'''
        img  = self.getImg(band,wvln)

        if imax is None: imax = np.nanmax(img)
        data = np.clip( 255.*(img-imin)/(imax-imin),0,255)

        from PIL import Image
        icon = Image.fromarray( np.uint8(data) )
        icon.save( 'img/%s.jpg' % self.imgID )
        return

if __name__ == '__main__':

    imgID = '1743920928_1'
    if len(sys.argv) > 1:
        imgID = sys.argv[1]

    vims = VIMS(imgID)
    vims.geoJSON(save=True)
    vims.saveJPG(wvln=2.02, imin=0.025)
