# -*- coding: utf-8 -*-
import os
import numpy as np
from osgeo import gdal, gdalconst

class GeoTiff(object):
    def __init__(self, fname):
        self.name = fname.replace('.tiff','').replace('.tif','')
        self.fname = self.name + '.tif'
        if self.isFile:
            self.read()

    def __str__(self):
        return self.fname
        
    def __repr__(self):
        return "<GeoTiff: {}>".format(str(self))

    @property
    def isFile(self):
        '''Check if the file exists'''
        return os.path.isfile(str(self))

    def read(self):
        '''Read the GeoTiff driver'''
        if not self.isFile:
            raise IOError('The GeoTiff file {} does not exist'.format(str(self)))
        ds = gdal.Open(self.fname, gdalconst.GA_ReadOnly)
        if ds.GetDriver().ShortName != 'GTiff':
            raise IOError('The File {} is not a GeoTiff'.format(str(self)))
        self.ds = ds

    @property
    def metadata(self):
        '''Get GeoTiff Metadata dict'''
        return self.ds.GetMetadata()

    @property
    def projection(self):
        '''Get GeoTiff WKT projection'''
        return self.ds.GetProjection()

    @property
    def bandCount(self):
        '''Get the number of bands'''
        return self.ds.RasterCount

    def band(self, i):
        '''Get band `i` data'''
        band = self.ds.GetRasterBand(i)
        data = band.ReadAsArray()
        data[data == band.GetNoDataValue()] = np.nan
        return data

    def bandMetadata(self, i):
        '''Get band `i` metadata'''
        return self.ds.GetRasterBand(i).GetMetadata()
