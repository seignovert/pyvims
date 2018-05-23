# -*- coding: utf-8 -*-
import os
import numpy as np
import cv2

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

def imgClip(img, imin=None, imax=None):
    '''Clip image [0-255] between imin/imax'''
    if imin is None:
        imin = np.nanmin(img)
    if imax is None:
        imax = np.nanmax(img)
    return np.uint8(np.clip(255.*(img-imin)/(imax-imin), 0, 255))

def imgInterp(img, height=256, hr='NORMAL', method=cv2.INTER_LANCZOS4):
    '''
    Interpolate image

    hr:
        High-Resolution mode in Sample direction ['NORMAL'|'HI-RES']
    
    method:
    - INTER_NEAREST - a nearest-neighbor interpolation
    - INTER_LINEAR - a bilinear interpolation
    - INTER_AREA - resampling using pixel area relation.
    - INTER_CUBIC - a bicubic interpolation over 4x4 pixel neighborhood
    - INTER_LANCZOS4 - a Lanczos interpolation over 8x8 pixel neighborhood
    '''
    if hr is None:
        return None
    if not height is None:
        hr = 1 if hr.upper() == 'NORMAL' else 2
        width = int((height * img.shape[1]) / img.shape[0] / hr)
        img = cv2.resize(img, (width, height), interpolation=method)
    return img

def imgEq(img, imin=None, imax=None):
    '''Locally equalize image'''
    # Create a CLAHE object.
    clahe = cv2.createCLAHE(clipLimit=1, tileGridSize=(2, 2))
    if len(img.shape) == 2: # GRAY
        if img.dtype != 'uint8':
            img = clipIMG(img, imin, imax)
        img = clahe.apply(img)
    elif len(img.shape) == 3:  # RGB [https://stackoverflow.com/a/47370615]
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        lab_planes = cv2.split(lab)
        lab_planes[0] = clahe.apply(lab_planes[0])
        lab = cv2.merge(lab_planes)
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    else:
        raise ValueError('Image shape must be 2 or 3')
    return img
