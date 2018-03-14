# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from datetime import datetime as dt
import pvl
from planetaryimage import CubeFile

from .vims_team  import VIMS_TEAM
from .vims_isis3 import VIMS_ISIS3
from .vims_qub   import VIMS_QUB
from .vims_lbl   import VIMS_LBL

class VIMS(object):
    '''Polymorphic VIMS class based on input file'''
    def __new__(cls, imgID, root=''):
        try:
            inst = VIMS_TEAM.__new__(VIMS_TEAM)
            inst.__init__(imgID, root)
        except NameError:
            try:
                inst = VIMS_ISIS3.__new__(VIMS_ISIS3)
                inst.__init__(imgID, root)
            except NameError:
                try:
                    inst = VIMS_QUB.__new__(VIMS_QUB)
                    inst.__init__(imgID, root)
                except NameError:
                    try:
                        inst = VIMS_LBL.__new__(VIMS_LBL)
                        inst.__init__(imgID, root)
                    except NameError:
                        raise NameError('CUB/QUB/LBL: %s not found' % imgID )
        inst.setNAV()
        return inst
