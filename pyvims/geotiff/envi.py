# -*- coding: utf-8 -*-

class ENVI(object):
    def __init__(self, NS, NL, NB, offset=0,
                 desc='ENVI File',
                 file_type='ENVI Standard',
                 data_type=4,
                 byte_order=0,
                 wvlns=[], units='Micrometers'):
        self.desc = desc
        self.samples = int(NS)
        self.lines = int(NL)
        self.bands = int(NB)
        self.offset = int(offset)
        self.file_type = file_type
        self.data_type = data_type
        self.byte_order = byte_order
        self.wvlns = wvlns
        self.wvlns_str = [str(w) for w in wvlns]
        self.wvln_units = units.title()

    @property
    def units(self):
        if self.wvln_units == 'Micrometers':
            return 'um'
        else:
            raise NotImplementedError('Unit {} is not implemented yet'.format(
                self.wvln_units))

    @property
    def bandNames(self):
        prec = 2
        return [
            'Band {} ({} {})'.format(int(i+1), round(self.wvlns[i], prec), self.units)
            for i in range(self.bands)
        ]

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
        out.append('wavelength = {{\n\t{}}}'.format(',\n\t'.join(self.wvlns_str)))
        return '\n'.join(out)
