# -*- coding: utf-8 -*-
import os

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
