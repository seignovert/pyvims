# -*- coding: utf-8 -*-
import os

from .vims_team import VIMS_TEAM

class VIMS_QUB(VIMS_TEAM):
    def __init__(self, imgID, root=''):
        VIMS_TEAM.__init__(self, imgID, root)
        return

    def __repr__(self):
        return "VIMS cube: %s [QUB]" % self.imgID

    @property
    def fname(self):
        '''Check if VIMS file exists.'''
        fname = self.root + 'v' + self.imgID + '.qub'
        if not os.path.isfile(fname):
            raise NameError('PDS QUB file was not found: %s' % fname)
        return fname
