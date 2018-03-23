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
    def __init__(self,imgID, root=''):
        VIMS_NAV.__init__(self, imgID, root=root)
        return

    def __repr__(self):
        return "VIMS ISIS3 geocube: %s" % self.imgID

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        fname = self.root + 'N' + self.imgID + '_ir.cub'
        if not os.path.isfile(fname):
            raise NameError('ISIS3 GeoCube file %s not found' % fname)
        return fname

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

        self.lat = cube[0]  # Pixel central latitude [North]
        self.lon = cube[1]  # % 360 # Pixel central longitude [East]
        self.res = cube[2]  # Phase angle [deg]
        self.inc = cube[3]  # Incidence angle [deg]
        self.eme = cube[4]  # Emission angle [deg]
        self.phase = cube[5]  # Phase angle [deg]

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
