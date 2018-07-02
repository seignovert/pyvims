# -*- coding: utf-8 -*-
from lxml import etree

class ArcMap(object):
    def __init__(self, wvlns):
        self.xml = etree.Element('PAMDataset')
        for i, w in enumerate(wvlns):
            band = etree.SubElement(self.xml, 'PAMRasterBand')
            band.set('band', str(int(i+1)))
            desc = etree.SubElement(band, 'Description')
            desc.text = 'Band {} / {} um'.format(i+1, w)

    def dump(self):
        return etree.tostring(self.xml, pretty_print=True)
