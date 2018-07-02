# -*- coding: utf-8 -*-
import numpy as np

class ENVI(object):
    def __init__(self, NS, NL, NB, offset=0,
                 desc='ENVI File',
                 file_type='ENVI Standard',
                 data_type=4,
                 byte_order=0,
                 wvlns=[],
                 units='Micrometers',
                 nbyline=8):
        self.desc = desc
        self.samples = int(NS)
        self.lines = int(NL)
        self.bands = int(NB)
        self.offset = int(offset)
        self.file_type = file_type
        self.data_type = data_type
        self.byte_order = byte_order
        self.wvlns = wvlns
        self.wvln_units = units.title()
        self.n = nbyline

    @property
    def units(self):
        if self.wvln_units == 'Micrometers':
            return 'um'
        else:
            raise NotImplementedError('Unit {} is not implemented yet'.format(
                self.wvln_units))

    @property
    def bandNames(self):
        bands = [ 'Band {}'.format(int(i+1)) for i in range(self.bands) ]
        return [', '.join(bands[i:i+self.n]) for i in np.arange(0, len(bands), self.n)]

    @property
    def wvlnNames(self):
        wvlns = [ str(w) for w in self.wvlns ]
        return [', '.join(wvlns[i:i+self.n]) for i in np.arange(0, len(wvlns), self.n)]

    def dump(self):
        out = ['ENVI']
        out.append('description = {{\n\t{}}}'.format(self.desc))
        out.append('samples = {}'.format(self.samples))
        out.append('lines   = {}'.format(self.lines))
        out.append('bands   = {}'.format(self.bands))
        out.append('header offset = {}'.format(self.offset))
        out.append('file type = {}'.format(self.file_type))
        out.append('data type = {}'.format(self.data_type))
        out.append('byte order = {}'.format(self.byte_order))
        out.append('wavelength units = {}'.format(self.wvln_units))
        out.append('band names = {{\n\t{}}}'.format(',\n\t'.join(self.bandNames)))
        out.append('wavelength = {{\n\t{}}}'.format(',\n\t'.join(self.wvlnNames)))
        return '\n'.join(out)
