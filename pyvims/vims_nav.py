# -*- coding: utf-8 -*-
import os
import numpy as np
from datetime import datetime as dt

from ._communs import getImgID

NaN = -99999.

# To remove NaN comparaison warnings
np.warnings.filterwarnings('ignore')

class VIMS_NAV(object):
    def __init__(self, imgID, root='', ir=None):
        '''
        Note:
        -----
        By befault the navigation is calculated on the IR FOV.
        In the cases where the acquisition VIS/IR mode are not the same,
        the navigation will differ between the VIS and the IR FOVs.

        In order to load the VIS FOV you only need to disable
        the `ir` flag by setting it to `False`.
        '''
        self.imgID = getImgID(imgID)
        self.root  = root
        self.setFOV(imgID, ir)
        self.readLBL()
        self.readNAV()
        return

    def __repr__(self):
        return "VIMS geocube: %s" % self.imgID

    def __str__(self):
        return self.imgID

    def setFOV(self, imgID, ir=None):
        '''
        Set the FOV flag (Default: IR=True).

        Note: If the `ir` flag is unset but the `imgID` contains the
        sub-string `vis`, then the `ir` is automatically disable.
        '''
        if ir is not None:
            self.ir = ir
        elif 'vis' in imgID:
            self.ir = False
        else:
            self.ir = True

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        if self.ir:
            fname = self.root + 'V' + self.imgID + '.nav'
        else:
            raise NotImplementedError('This GeoCube is only available for the IR FOV')
        if not os.path.isfile(fname):
            raise NameError('GeoCube file %s not found' % fname)
        return fname

    def readLBL(self):
        '''Read VIMS geocube LBL'''
        with open(self.fname) as f:
            lbl = {}; self.IDFoffset = 0
            for line in f.readlines():
                self.IDFoffset += len(line)
                if line == 'END\n' or line == 'FIN\n':
                    break
                elif line == 'END\r\n' or line == 'FIN\r\n':
                    self.IDFoffset += 1
                    break
                elif 'AXIS_NAME' in line:
                    axisName = line.rstrip('\r\n')\
                                   .split(' = ')[1]\
                                   .replace('(','')\
                                   .replace(')','')\
                                   .split(',')

                elif 'CORE_ITEMS' in line:
                    coreItems = line.rstrip('\r\n')\
                                    .split('=')[1]\
                                    .replace('(','')\
                                    .replace(')','')\
                                    .split(',')

                elif 'CORE_ITEM_BYTES' in line:
                    self.coreItemBytes = int(line.rstrip('\r\n')
                                                 .split(' = ')[1])

                elif 'CORE_ITEM_TYPE' in line:
                    self.coreItemType = line.rstrip('\r\n')\
                                   .split(' = ')[1]

                elif 'INSTRUMENT_HOST_NAME' in line:
                    self.obs = line.rstrip('\r\n')\
                                   .split(' = ')[1]\
                                   .replace('"', '')

                elif 'INSTRUMENT_ID' in line:
                    self.inst = line.rstrip('\r\n')\
                                    .split(' = ')[1]\
                                    .replace('"', '')

                elif 'TARGET_NAME' in line:
                    self.target = line.rstrip('\r\n')\
                                      .split(' = ')[1]\
                                      .replace('"','')

                elif 'START_TIME' in line and (not 'NATIVE' in line) and (not 'EARTH_RECEIVED' in line):
                    self.start = dt.strptime(
                                    line.rstrip('\r\n')\
                                    .split(' = ')[1]\
                                    .replace('"',''),
                                    '%Y-%jT%H:%M:%S.%fZ')

                elif 'STOP_TIME' in line and (not 'NATIVE' in line) and (not 'EARTH_RECEIVED' in line):
                    self.stop = dt.strptime(
                                    line.rstrip('\r\n')\
                                    .split(' = ')[1]\
                                    .replace('"',''),
                                    '%Y-%jT%H:%M:%S.%fZ')

                elif '.ker' in line:
                    self.flyby = int(line.rstrip('\r\n')[-8:-5])

        for ii, axis in enumerate(axisName):
            if axis == 'SAMPLE':
                self.NS = int(coreItems[ii])
            elif axis == 'LINE':
                self.NL = int(coreItems[ii])
            elif axis == 'BAND':
                self.NB = int(coreItems[ii])

        self.dtime  = (self.stop - self.start)/2 + self.start
        self.time   = self.dtime.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.year   = self.dtime.year
        self.doy    = int(self.dtime.strftime('%j'))
        self.year_d = self.year + (self.doy-1)/365. # Decimal year [ISSUE: doest not apply take into account bissextile years]
        self.date   = self.dtime.strftime('%Y/%m/%d')

        return

    def readNAV(self):
        '''Read VIMS geocube data'''
        # Read binary file
        if self.coreItemType == 'SUN_INTEGER':
            arch = '>' # Big endian
        else:
            arch = '<' # Little endian

        if self.coreItemBytes == 2:
            byte = 'i2'
        elif self.coreItemBytes == 4:
            byte = 'f'
        else:
            raise ValueError('Unknown CORE_ITEM_BYTES')

        dtype = np.dtype(arch+byte)
        nbytes = self.NS * self.NL * self.coreItemBytes

        shape = (self.NL, self.NS)

        with open(self.fname, 'rb') as f:
            f.seek(self.IDFoffset+2, os.SEEK_SET) # Skip Ascii header
            self.lon = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) #% 360 # Pixel central longitude [East]
            self.lat = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) # Pixel central latitude [North]
            self.inc = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) # Incidence angle [deg]
            self.eme = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) # Emergence angle [deg]
            self.phase = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) # Phase angle [deg]
            f.read(nbytes*9) # Slip cornes lon/lat and altitude
            self.res = np.frombuffer(f.read(nbytes),dtype=dtype).reshape(shape) # Phase angle [deg]

        self.lon.setflags(write=1)
        self.lat.setflags(write=1)
        self.inc.setflags(write=1)
        self.eme.setflags(write=1)
        self.phase.setflags(write=1)
        self.res.setflags(write=1)

        self.nan = (self.lon == NaN)
        self.lon[self.nan] = np.nan
        self.lat[self.nan] = np.nan
        self.inc[self.nan] = np.nan
        self.eme[self.nan] = np.nan
        self.phase[self.nan] = np.nan
        self.res[self.nan] = np.nan
        return

    @property
    def specular(self):
        return (np.abs(self.inc - self.eme) < 1) & \
                (np.abs(self.phase-(self.inc+self.eme)) < 1) & \
                (self.inc < 92)
