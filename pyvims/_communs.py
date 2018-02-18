# -*- coding: utf-8 -*-
import os
import numpy as np

def getImgID(imgID):
    '''Extract img identification number'''
    return imgID.lower()\
                .split(os.sep)[-1]\
                .replace('cm_','')\
                .replace('_ir','')\
                .replace('_vis','')\
                .replace('.cub','')\
                .replace('.qub','')\
                .replace('.nav','')\
                .replace('.lbl','')\
                .replace('c','')\
                .replace('v','')

def clipIMG(img, imin=0, imax=None):
    '''Clip image [0-255] between imin/imax'''
    if imax is None:
        imax = np.nanmax(img)
    return np.uint8(np.clip(255.*(img-imin)/(imax-imin), 0, 255))
