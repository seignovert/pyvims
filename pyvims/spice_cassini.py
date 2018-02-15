#!/bin/python

import os
import spiceypy as spice

# Kernels root directory
DIR_KERNELS = 'kernels/'

# Leapsecond [generic_kernels/lsk/naif0012.tls]
LSK = 'naif0012.tls'

# Spacecraft clock [CASSINI/kernels/sclk/cas00171.tsc]
SCLk = 'cas00171.tsc'

# Planetary Constants [generic_kernels/lsk/naif0012.tls]
PCK = 'pck00010.tpc'

# Spacecraft and Planet Ephemeris [CASSINI/kernels/spk/171215R_SCPSEops_97288_17258.bsp]
PSK = '171215R_SCPSEops_97288_17258.bsp'


class SPICE_CASSINI(object):
    def __init__(self):
        self.obs = 'CASSINI'
        self.sc = -82 # spice.bodn2c(

        # Kernels root directory
        self.__dir = DIR_KERNELS
        # generic_kernels/lsk/naif0012.tls
        self.__lsk = LSK
        # CASSINI/kernels/sclk/cas00171.tsc
        self.__sclk = SCLk
        # generic_kernels/lsk/naif0012.tls
        self.__pck = PCK
        # CASSINI/kernels/spk/171215R_SCPSEops_97288_17258.bsp
        self.__psk = PSK

        self.loaded = False
        return
        
    def __repr__(self):
        return 'Cassini Spice Kernels tools'

    def __del__(self):
        self.clear()

    @property
    def dir(self):
        '''Kernels root directory'''
        return self.__dir

    @dir.setter
    def lsk(self, dir):
        '''Reset dir root directory'''
        self.__dir = dir

    @property
    def lsk(self):
        '''Leapsecond kernel'''
        return self.__lsk

    @lsk.setter
    def lsk(self, lsk):
        '''Reset leapsecond kernel'''
        self.__lsk = lsk

    @property
    def sclk(self):
        '''Spacecraft clock kernel'''
        return self.__sclk

    @sclk.setter
    def sclk(self, sclk):
        '''Reset spacecraft clock kernel'''
        self.__sclk = sclk

    @property
    def pck(self):
        '''Planetary Constants kernel'''
        return self.__pck

    @pck.setter
    def pck(self, pck):
        '''Reset planetary Constants kernel'''
        self.__pck = pck

    @property
    def psk(self):
        '''Spacecraft and Planet Ephemeris kernel'''
        return self.__psk

    @psk.setter
    def psk(self, psk):
        '''Reset Spacecraft and Planet Ephemeris kernel'''
        self.__psk = psk

    def load(self):
        '''Load kernels'''
        if not os.path.exists(self.dir):
            raise IOError('Kernel folder `%s` does not exist' % self.dir)
        if not os.path.isfile(self.dir + self.lsk):
            raise IOError('%s not found' % (self.dir + self.lsk) )
        if not os.path.isfile(self.dir + self.sclk):
            raise IOError('%s not found' % (self.dir + self.sclk) )
        if not os.path.isfile(self.dir + self.pck):
            raise IOError('%s not found' % (self.dir + self.pck) )
        if not os.path.isfile(self.dir + self.psk):
            raise IOError('%s not found' % (self.dir + self.psk) )
        spice.furnsh(self.dir + self.lsk)
        spice.furnsh(self.dir + self.sclk)
        spice.furnsh(self.dir + self.pck)
        spice.furnsh(self.dir + self.psk)

    def clear(self):
        '''Clear spice kernel pool'''
        spice.kclear()
        self.loaded = False

    def reload(self):
        '''Reload kernels'''        
        self.clear()
        self.load()
        self.loaded = True

    def toUTC(self, sclk, fmt='ISOC', prec=5):
        '''Convert Spacecraft clock time to UTC'''
        if not self.loaded:
            self.load()
        if isinstance(sclk, (int, float)):
            sclk = '1/%f' % sclk
        elif '_' in sclk:
            sclk = '1/' + sclk.split('_')[0]
        return spice.et2utc(spice.scs2e(self.sc, sclk), fmt, prec)

    def toSCL(self, utc):
        '''Convert UTC to Spacecraft clock time'''
        if not self.loaded:
            self.load()
        return spice.sce2s(self.sc, spice.str2et(utc))
