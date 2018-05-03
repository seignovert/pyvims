# -*- coding: utf-8 -*-
import os
import numpy as np
from datetime import datetime as dt
import pvl

from .vims_class import VIMS_OBJ

class VIMS_LBL(VIMS_OBJ):
    def __init__(self, imgID, root=''):
        VIMS_OBJ.__init__(self, imgID, root)
        self.readLBL()
        return

    def __repr__(self):
        return "VIMS cube: %s [LBL]" % self.imgID

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        fname = self.root + 'v' + self.imgID + '.lbl'
        if not os.path.isfile(fname):
            raise NameError('LBL file was not found: %s' % fname)
        return fname

    def readLBL(self):
        '''Read VIMS LBL header'''
        self.lbl = pvl.load(self.fname)

        for ii, axis in enumerate(self.lbl['SPECTRAL_QUBE']['AXIS_NAME']):
            if axis == 'SAMPLE':
                self.NS = int(self.lbl['SPECTRAL_QUBE']['CORE_ITEMS'][ii])
            elif axis == 'LINE':
                self.NL = int(self.lbl['SPECTRAL_QUBE']['CORE_ITEMS'][ii])
            elif axis == 'BAND':
                self.NB = int(self.lbl['SPECTRAL_QUBE']['CORE_ITEMS'][ii])

        self.obs    = self.lbl['INSTRUMENT_HOST_NAME']
        self.inst   = self.lbl['INSTRUMENT_ID']
        self.target = self.lbl['TARGET_NAME']
        self.expo = {'IR': self.lbl['EXPOSURE_DURATION'][0], 'VIS': self.lbl['EXPOSURE_DURATION'][1]}
        self.mode = {'IR': self.lbl['SAMPLING_MODE_ID'][0], 'VIS': self.lbl['SAMPLING_MODE_ID'][1]}
        self.seq    = self.lbl['SEQUENCE_ID']
        self.seq_title = self.lbl['SEQUENCE_TITLE']
        self.start  = self.lbl['START_TIME']
        self.stop   = self.lbl['STOP_TIME']
        self.dtime  = (self.stop - self.start)/2 + self.start
        self.time   = self.dtime.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.year   = self.dtime.year
        self.doy    = int(self.dtime.strftime('%j'))
        self.year_d = self.year + (self.doy-1)/365. # Decimal year [ISSUE: doest not apply take into account bissextile years]
        self.date   = self.dtime.strftime('%Y/%m/%d')

        self.wvlns = None
        self.bands = None
        return

    def readCUB(self):
        '''Read VIMS CUB data file - Empty'''
        raise NotImplementedError("LBL file does not contain data.")
