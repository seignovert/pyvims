# -*- coding: utf-8 -*-
import os
import numpy as np
from datetime import datetime as dt
import pvl
from planetaryimage import CubeFile

from ._communs import getImgID
from .vims_nav import VIMS_NAV

NaN = -99999.

# To remove NaN comparaison warnings
np.warnings.filterwarnings('ignore')

class VIMS_NAV_ISIS3(VIMS_NAV):
    def __init__(self,imgID, root='', ir=None):
        '''
        Note:
        -----
        By befault the navigation is calculated on the IR FOV.
        In the cases where the acquisition VIS/IR mode are not the same,
        the navigation will differ between the VIS and the IR FOVs.

        In order to load the VIS FOV you only need to disable
        the `ir` flag by setting it to `False`.
        '''
        VIMS_NAV.__init__(self, imgID, root=root, ir=ir)
        return

    def __repr__(self):
        return "VIMS ISIS3 geocube: %s" % self.imgID

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        try:
            if self.ir:
                try:
                    return self.fname_ir
                except NameError as e:
                    print('WARNING: {}'.format(e))
                    self.ir = False
                    return self.fname_vis
            else:
                try:
                    return self.fname_vis
                except NameError as e:
                    print('WARNING: {}'.format(e))
                    self.ir = True
                    return self.fname_ir
        except NameError:
            raise NameError('Neither ISIS3 VIS nor IR {} NAV CUBs files were found %s'.format(self.imgID))

    @property
    def fname_vis(self):
        '''Check if VIMS VIS NAV file exists.'''
        fname_vis = self.root + 'N' + self.imgID + '_vis.cub'
        if not os.path.isfile(fname_vis):
            raise NameError('Missing {} VIS NAV CUB file'.format(self.imgID))
        return fname_vis

    @property
    def fname_ir(self):
        '''Check if VIMS VIS NAV file exists.'''
        fname_ir = self.root + 'N' + self.imgID + '_ir.cub'
        if not os.path.isfile(fname_ir):
            raise NameError('Missing {} IR NAV CUB file'.format(self.imgID))
        return fname_ir

    def readLBL(self):
        '''Read VIMS ISIS3 geocube LBL'''
        self.lbl = pvl.load(self.fname)['IsisCube']

        self.NS = int(self.lbl['Core']['Dimensions']['Samples'])
        self.NL = int(self.lbl['Core']['Dimensions']['Lines'])
        self.NB = int(self.lbl['Core']['Dimensions']['Bands'])
        self.obs = self.lbl['Instrument']['SpacecraftName']
        self.inst = self.lbl['Instrument']['InstrumentId']
        self.target = self.lbl['Instrument']['TargetName']
        self.seq = self.lbl['Archive']['SequenceId']
        self.seq_title = self.lbl['Archive']['SequenceTitle']
        self.start = self.lbl['Instrument']['StartTime']
        self.stop = self.lbl['Instrument']['StopTime']
        self.dtime = (self.stop - self.start)/2 + self.start
        self.time = self.dtime.strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.year = self.dtime.year
        self.doy = int(self.dtime.strftime('%j'))
        self.year_d = self.year +  (self.doy-1) / 365.  # Decimal year [ISSUE: doest not apply take into account bissextile years]
        self.date = self.dtime.strftime('%Y/%m/%d')
        return

    def readNAV(self):
        '''Read VIMS geocube data'''
        cube = np.array(CubeFile.open(self.fname).data)

        for ii, frame in enumerate(self.lbl['BandBin']['Name']):
            if frame == 'Latitude':
                self.lat = cube[ii]  # Pixel central latitude [North]
            elif frame == 'Longitude':
                self.lon = cube[ii]  # % 360 # Pixel central longitude [East]
            elif frame == 'Pixel Resolution':
                self.res = cube[ii]*1.e-3  # Pixel resolution [km/pix]
            elif frame == 'Incidence Angle':
                self.inc = cube[ii]  # Incidence angle [deg]
            elif frame == 'Emission Angle':
                self.eme = cube[ii]  # Emission angle [deg]
            elif frame == 'Phase Angle':
                self.phase = cube[ii]  # Phase angle [deg]
            else:
                raise ValueError('ISIS NAV frame name (%s) is unknown' % frame)

        self.nan = (self.lon < NaN)
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
