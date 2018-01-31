# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from datetime import datetime as dt
import pvl
from planetaryimage import CubeFile

from .vims_class import VIMS_OBJ

class VIMS_ISIS3(VIMS_OBJ):
    def __init__(self, imgID, root='', ir=True):
        VIMS_OBJ.__init__(self, imgID, root)
        self.ir = ir
        self.readLBL()
        self.readCUB()
        return

    def __repr__(self):
        return "VIMS cube: %s [ISIS3]" % self.imgID

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        ext = '_ir' if self.ir else '_vis'
        fname = self.root + 'C' + self.imgID + ext + '.cub'
        if not os.path.isfile(fname):
            raise NameError('ISIS CUB file was not found: %s')
        return fname

    def readLBL(self):
        '''Read VIMS LBL header'''
        self.lbl = pvl.load(self.fname)['IsisCube']

        self.NS     = int(self.lbl['Core']['Dimensions']['Samples'])
        self.NL     = int(self.lbl['Core']['Dimensions']['Lines'])
        self.NB     = int(self.lbl['Core']['Dimensions']['Bands'])
        self.obs    = self.lbl['Instrument']['SpacecraftName']
        self.inst   = self.lbl['Instrument']['InstrumentId']
        self.target = self.lbl['Instrument']['TargetName']
        if self.ir:
            self.expo = self.lbl['Instrument']['ExposureDuration'][0][0]
        else:
            self.expo = self.lbl['Instrument']['ExposureDuration'][1][0]
        self.start  = self.lbl['Instrument']['StartTime']
        self.stop   = self.lbl['Instrument']['StopTime']
        self.dtime  = (self.stop - self.start)/2 + self.start
        self.time   = self.dtime.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.year   = self.dtime.year
        self.doy    = int(self.dtime.strftime('%j'))
        self.year_d = self.year + (self.doy-1)/365. # Decimal year [ISSUE: doest not apply take into account bissextile years]
        self.date   = self.dtime.strftime('%Y/%m/%d')

        self.wvlns = np.array(self.lbl['BandBin']['Center'])
        self.bands = np.array(self.lbl['BandBin']['OriginalBand'])
        return

    def readCUB(self):
        '''Read VIMS CUB data file'''
        self.cube = np.array( CubeFile.open(self.fname).data )
        return
