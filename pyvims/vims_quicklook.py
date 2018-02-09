#!/bin/python

import sys
import numpy as np

from .vims import VIMS

class VIMS_QUICKLOOK(VIMS):
    def __init__(self,imgID, root=''):
        VIMS.__init__(self, imgID, root)
        return
