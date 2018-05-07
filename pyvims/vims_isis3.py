# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from datetime import datetime as dt
import pvl
from planetaryimage import CubeFile

from .vims_class import VIMS_OBJ

class VIMS_ISIS3(VIMS_OBJ):
    def __init__(self, imgID, root=''):
        VIMS_OBJ.__init__(self, imgID, root)
        self.readLBL()
        self.readCUB()
        return

    def __repr__(self):
        return "VIMS cube: %s [ISIS3]" % self.imgID

    @property
    def fname(self):
        '''Check if VIMS VIS/IR files exists.'''
        return self.fname_ir, self.fname_vis

    @property
    def fname_vis(self):
        '''Check if VIMS VIS file exists.'''
        fname_vis = self.root + 'C' + self.imgID + '_vis.cub'
        if not os.path.isfile(fname_vis):
            raise NameError('ISIS VIS CUB file was not found: %s' % fname_vis)
        return fname_vis

    @property
    def fname_ir(self):
        '''Check if VIMS file exists.'''
        fname_ir = self.root + 'C' + self.imgID + '_ir.cub'
        if not os.path.isfile(fname_ir):
            raise NameError('ISIS IR CUB file was not found: %s' % fname_ir)
        return fname_ir

    def readLBL(self):
        '''Read VIMS LBL header'''
        try:
            self.lbl = pvl.load(self.fname_ir)['IsisCube']
            sampling_IR = self.lbl['Instrument']['SamplingMode']
            wvlns_IR = self.lbl['BandBin']['Center']
            bands_IR = self.lbl['BandBin']['OriginalBand']
            try:
                lbl_vis = pvl.load(self.fname_vis)['IsisCube']
                sampling_VIS = lbl_vis['Instrument']['SamplingMode']
                wvlns_VIS = lbl_vis['BandBin']['Center']
                bands_VIS = lbl_vis['BandBin']['OriginalBand']
            except NameError:
                print('WARNING: Missing {} VIS CUB file'.format(self.imgID))
                sampling_VIS = None
                wvlns_VIS = [np.nan]*96
                bands_VIS = [np.nan]*96
        except NameError:
            print('WARNING: Missing {} IR CUB file'.format(self.imgID))
            sampling_IR = None
            wvlns_IR = [np.nan]*256
            bands_IR = [np.nan]*256
            try:
                self.lbl = pvl.load(self.fname_vis)['IsisCube']
                sampling_VIS = self.lbl['Instrument']['SamplingMode']
                wvlns_VIS = self.lbl['BandBin']['Center']
                bands_VIS = self.lbl['BandBin']['OriginalBand']
            except NameError:
                raise NameError('Neither ISIS3 VIS nor IR {} CUBs files were found %s'.format(self.imgID))

        self.NS     = int(self.lbl['Core']['Dimensions']['Samples'])
        self.NL     = int(self.lbl['Core']['Dimensions']['Lines'])
        self.NB     = int(self.lbl['Core']['Dimensions']['Bands'])
        self.obs    = self.lbl['Instrument']['SpacecraftName']
        self.inst   = self.lbl['Instrument']['InstrumentId']
        self.target = self.lbl['Instrument']['TargetName']
        self.expo   = {key: val for val, key in self.lbl['Instrument']['ExposureDuration']}      
        self.mode   = {'IR': sampling_IR, 'VIS': sampling_VIS}
        self.seq    = self.lbl['Archive']['SequenceId']
        self.seq_title = self.lbl['Archive']['SequenceTitle']
        self.start  = self.lbl['Instrument']['StartTime']
        self.stop   = self.lbl['Instrument']['StopTime']
        self.dtime  = (self.stop - self.start)/2 + self.start
        self.time   = self.dtime.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.year   = self.dtime.year
        self.doy    = int(self.dtime.strftime('%j'))
        self.year_d = self.year + (self.doy-1)/365. # Decimal year [ISSUE: doest not apply take into account bissextile years]
        self.date   = self.dtime.strftime('%Y/%m/%d')

        self.wvlns_ir = np.array(wvlns_IR)
        self.bands_ir = np.array(bands_IR)
        self.wvlns_vis = np.array(wvlns_VIS)
        self.bands_vis = np.array(bands_VIS)

        if sampling_IR is not None:
            self.shift_ir = np.mean(np.subtract(self.lbl['BandBin']['MissionAverage'],self.wvlns_ir))

        self.wvlns = np.concatenate((self.wvlns_vis, self.wvlns_ir), axis=0)
        self.bands = np.concatenate((self.bands_vis, self.bands_ir), axis=0)
        return

    def readCUB(self):
        '''Read VIMS CUB data file'''
        try:
            self.cube_vis = np.array(CubeFile.open(self.fname_vis).data)
        except NameError:
            self.cube_vis = np.array([[[np.nan]*self.NS]*self.NL]*96)

        try:
            self.cube_ir = np.array(CubeFile.open(self.fname_ir).data)
        except NameError:
            self.cube_ir = np.array([[[np.nan]*self.NS]*self.NL]*256)

        self.cube = np.concatenate((self.cube_vis, self.cube_ir), axis=0)
        return
