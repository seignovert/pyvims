# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from datetime import datetime as dt
import pvl

from .vims_class import VIMS_OBJ
from .geotiff import GeoTiff

class VIMS_GEOTIFF(VIMS_OBJ):
    def __init__(self, imgID, root=''):
        VIMS_OBJ.__init__(self, imgID, root)
        self.geotiff = GeoTiff(self.fname)
        self.readLBL()
        self.readCUB()
        return

    def __repr__(self):
        return "VIMS cube: %s [GEOTIFF]" % self.imgID

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        fname = self.root + self.imgID + '.tif'
        if not os.path.isfile(fname):
            raise NameError('GeoTiff file not found: %s' % fname)
        return fname

    def readLBL(self):
        '''Read VIMS LBL header'''
        metadata = self.geotiff.metadata
        lbl = pvl.loads(metadata['ISIS_CUBE_HEADER'])
        sampling_VIS, sampling_IR = metadata['VIMS_SAMPLING_VIS_IR'].split(',')

        self.NS     = int(lbl['Core']['Dimensions']['Samples'])
        self.NL     = int(lbl['Core']['Dimensions']['Lines'])
        self.NB     = int(self.geotiff.bandCount)
        self.obs    = lbl['Instrument']['SpacecraftName']
        self.inst   = lbl['Instrument']['InstrumentId']
        self.target = lbl['Instrument']['TargetName']
        self.expo   = {key: val for val, key in lbl['Instrument']['ExposureDuration']}      
        self.mode   = {'IR': sampling_IR, 'VIS': sampling_VIS}
        self.seq    = lbl['Archive']['SequenceId']
        self.seq_title = lbl['Archive']['SequenceTitle']
        self.start  = lbl['Instrument']['StartTime']
        self.stop   = lbl['Instrument']['StopTime']
        self.dtime  = (self.stop - self.start)/2 + self.start
        self.time   = self.dtime.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.year   = self.dtime.year
        self.doy    = int(self.dtime.strftime('%j'))
        self.year_d = self.year + (self.doy-1)/365. # Decimal year [ISSUE: doest not apply take into account bissextile years]
        self.date   = self.dtime.strftime('%Y/%m/%d')

        self.bands = np.nan * np.empty((self.NB))
        self.wvlns = np.nan * np.empty((self.NB))
        for i in range(self.NB):
            self.bands[i] = i+1
            self.wvlns[i] = float(self.geotiff.metadataBand(i+1)['GTIFF_DIM_wvln'])
        return

    def readCUB(self):
        '''Read VIMS CUB data file'''
        self.cube = np.nan * np.empty((self.NB, self.NL, self.NS))
        for i in range(self.NB):
            self.cube[i, :, :] = self.geotiff.band(i+1)
        return
