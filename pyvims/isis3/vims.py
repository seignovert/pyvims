# -*- coding: utf-8 -*-
import os

from .._communs import getImgID

from .isis3 import ProcessError, ISISError, call

VERBOSE = True

QUB = 'QUB' if 'VIMS_QUB' not in os.environ else os.environ['VIMS_QUB']
CUB = 'CUB' if 'VIMS_CUB' not in os.environ else os.environ['VIMS_CUB']
CAL = 'CAL' if 'VIMS_CAL' not in os.environ else os.environ['VIMS_CAL']
NAV = 'NAV' if 'VIMS_NAV' not in os.environ else os.environ['VIMS_NAV']
DNS = 'DNS' if 'VIMS_DNS' not in os.environ else os.environ['VIMS_DNS']
CLN = 'CLN' if 'VIMS_CLN' not in os.environ else os.environ['VIMS_CLN']


def isVIS(channel):
    '''Check if VIMS channel is VIS (visible) or IR (infra-red)'''
    ch = channel.upper()
    if ch == 'VIS':
        return True
    elif ch == 'IR':
        return False
    else:
        raise KeyError('Unknown VIMS channel [VIS|IR]: {}'.format(channel))

class VIMSError(ISISError):
    def __init__(self, returncode, cmd, vims):
        super(VIMSError, self).__init__(returncode, cmd, vims)

class ISIS3_VIMS(object):
    def __init__(self, imgID, qub=QUB, cub=CUB,
                 cal=CAL, nav=NAV,
                 dns=DNS, cln=CLN,
                 verbose=VERBOSE):

        self.id = getImgID(imgID)
        self._qub = qub
        self._cub = cub
        self._cal = cal
        self._nav = nav
        self._dns = dns
        self._cln = cln
        self.verbose = verbose

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<[ISIS3] VIMS: {}>'.format(self)

    @property
    def qub(self):
        return os.path.join(self._qub, 'v'+self.id+'.qub')

    @property
    def vis(self):
        return os.path.join(self._cub, 'v'+self.id+'_vis.cub')

    @property
    def cal_vis(self):
        return os.path.join(self._cal, 'C'+self.id+'_vis_cal.cub')

    @property
    def nav_vis(self):
        return os.path.join(self._nav, 'N'+self.id+'_vis.cub')

    @property
    def dns_vis(self):
        return os.path.join(self._dns, 'C'+self.id+'_vis_dns.cub')

    @property
    def cln_vis(self):
        return os.path.join(self._cln, 'C'+self.id+'_vis.cub')

    @property
    def ir(self):
        return os.path.join(self._cub, 'v'+self.id+'_ir.cub')

    @property
    def cal_ir(self):
        return os.path.join(self._cal, 'C'+self.id+'_ir_cal.cub')

    @property
    def nav_ir(self):
        return os.path.join(self._nav, 'N'+self.id+'_ir.cub')

    @property
    def dns_ir(self):
        return os.path.join(self._dns, 'C'+self.id+'_ir_dns.cub')

    @property
    def cln_ir(self):
        return os.path.join(self._cln, 'C'+self.id+'_ir.cub')

# ISIS functions
def vims2isis(vims, cub=CUB, verbose=VERBOSE):
    if not isinstance(vims, ISIS3_VIMS):
        vims = ISIS3_VIMS(vims, cub=cub, verbose=verbose)
    try:
        call([
            'vims2isis',
            'from={}'.format(vims.qub),
            'ir={}'.format(vims.ir),
            'vis={}'.format(vims.vis)
        ])

        if vims.verbose:
            print('-> VIS/IR CUB {} created'.format(vims.id))

    except ProcessError as e:
        if vims.verbose:
            print("STDOUT: vims2isis - {}\n{}".format(vims.id, e.stdout))
            print("STDERR: vims2isis - {}\n{}".format(vims.id, e.stderr))
        else:
            raise VIMSError(e.returncode, 'vims2isis', vims.id)


def spiceinit(vims, cub=CUB, verbose=VERBOSE):
    spiceinit_ch(vims, 'VIS', cub=cub, verbose=verbose)
    spiceinit_ch(vims, 'IR', cub=cub, verbose=verbose)


def spiceinit_ch(vims, channel='IR', cub=CUB, verbose=VERBOSE):
    if not isinstance(vims, ISIS3_VIMS):
        vims = ISIS3_VIMS(vims, cub=cub, verbose=verbose)
    try:
        call([
            'spiceinit',
            'from={}'.format(vims.vis if isVIS(channel) else vims.ir),
        ])

        if vims.verbose:
            print('-> CUB {} ({}) spice init succeded'.format(vims.id, channel))

    except ProcessError as e:
        if vims.verbose:
            print("STDOUT: spiceinit ({}) - {}\n{}".format(channel, vims.id, e.stdout))
            print("STDERR: spiceinit ({}) - {}\n{}".format(channel, vims.id, e.stderr))
        else:
            raise VIMSError(e.returncode, 'spiceinit ({})'.format(channel, vims.id))


def vimscal(vims, cal=CAL, verbose=VERBOSE):
    vimscal_ch(vims, 'VIS', cal=cal, verbose=verbose)
    vimscal_ch(vims, 'IR', cal=cal, verbose=verbose)


def vimscal_ch(vims, channel='IR', cal=CAL, verbose=VERBOSE):
    if not isinstance(vims, ISIS3_VIMS):
        vims = ISIS3_VIMS(vims, cal=cal, verbose=verbose)
    try:
        call([
            'vimscal',
            'from={}'.format(vims.vis if isVIS(channel) else vims.ir),
            'to={}'.format(vims.cal_vis if isVIS(channel) else vims.cal_ir),
            'units=IOF',
        ])

        if vims.verbose:
            print('-> CAL {} ({}) created'.format(vims.id, channel))

    except ProcessError as e:
        if vims.verbose:
            print("STDOUT: vimscal ({}) - {}\n{}".format(channel, vims.id, e.stdout))
            print("STDERR: vimscal ({}) - {}\n{}".format(channel, vims.id, e.stderr))
        else:
            raise VIMSError(e.returncode, 'vimscal ({})'.format(channel), vims.id)


def phocube(vims, nav=CAL, verbose=VERBOSE):
    phocube_ch(vims, 'VIS', nav=nav, verbose=verbose)
    phocube_ch(vims, 'IR', nav=nav, verbose=verbose)


def phocube_ch(vims, channel='IR', nav=CAL, verbose=VERBOSE):
    if not isinstance(vims, ISIS3_VIMS):
        vims = ISIS3_VIMS(vims, nav=nav, verbose=verbose)
    try:
        call([
            'phocube',
            'from={}+1'.format(vims.cal_vis if isVIS(channel) else vims.cal_ir),
            'to={}'.format(vims.nav_vis if isVIS(channel) else vims.nav_ir),
            'latitude=true',
            'longitude=true',
            'pixelresolution=true',
            'incidence=true',
            'emission=true',
            'phase=true',
        ])

        if vims.verbose:
            print('-> NAV {} ({}) created'.format(vims.id, channel))

    except ProcessError as e:
        if vims.verbose:
            print("STDOUT: vimscal ({}) - {}\n{}".format(channel, vims.id, e.stdout))
            print("STDERR: vimscal ({}) - {}\n{}".format(channel, vims.id, e.stderr))
        else:
            raise VIMSError(e.returncode, 'phocube ({})'.format(channel), vims.id)


def noisefilter(vims, dns=DNS, verbose=VERBOSE):
    noisefilter_ch(vims, 'VIS', dns=dns, verbose=verbose)
    noisefilter_ch(vims, 'IR', dns=dns, verbose=verbose)


def noisefilter_ch(vims, channel='IR', dns=DNS, verbose=VERBOSE):
    if not isinstance(vims, ISIS3_VIMS):
        vims = ISIS3_VIMS(vims, dns=dns, verbose=verbose)
    try:
        call([
            'noisefilter',
            'from={}'.format(vims.cal_vis if isVIS(channel) else vims.cal_ir),
            'to={}'.format(vims.dns_vis if isVIS(channel) else vims.dns_ir),
            'toldef=stddev',
            'tolmin=2.5',
            'tolmax=2.5',
            'replace=null',
            'samples=5',
            'lines=5',
        ])

        if vims.verbose:
            print('-> DNS {} ({}) created'.format(vims.id, channel))

    except ProcessError as e:
        if vims.verbose:
            print("STDOUT: noisefilter ({}) - {}\n{}".format(channel, vims.id, e.stdout))
            print("STDERR: noisefilter ({}) - {}\n{}".format(channel, vims.id, e.stderr))
        else:
            raise VIMSError(e.returncode, 'noisefilter ({})'.format(channel), vims.id)


def lowpass(vims, cln=CLN, verbose=VERBOSE):
    lowpass_ch(vims, 'VIS', cln=cln, verbose=verbose)
    lowpass_ch(vims, 'IR', cln=cln, verbose=verbose)


def lowpass_ch(vims, channel='IR', cln=CLN, verbose=VERBOSE):
    if not isinstance(vims, ISIS3_VIMS):
        vims = ISIS3_VIMS(vims, cln=cln, verbose=verbose)
    try:
        call([
            'lowpass',
            'from={}'.format(vims.dns_vis if isVIS(channel) else vims.dns_ir),
            'to={}'.format(vims.cln_vis if isVIS(channel) else vims.cln_ir),
            'samples=3',
            'lines=3',
            'filter=outside',
            'null=yes',
            'hrs=no',
            'his=no',
            'lrs=no',
            'replacement=center',
        ])

        if vims.verbose:
            print('-> CLN {} ({}) created'.format(vims.id, channel))

    except ProcessError as e:
        if vims.verbose:
            print("STDOUT: lowpass ({}) - {}\n{}".format(channel, vims.id, e.stdout))
            print("STDERR: lowpass ({}) - {}\n{}".format(channel, vims.id, e.stderr))
        else:
            raise VIMSError(e.returncode, 'lowpass ({})'.format(channel), vims.id)


def calibrate(imgID, qub=QUB, cub=CUB,
              cal=CAL, nav=NAV,
              dns=DNS, cln=CLN,
              verbose=VERBOSE):
    '''Full VIMS calibration and denoise'''

    vims = ISIS3_VIMS(imgID, qub=qub, cub=cub,
                      cal=cal, nav=nav,
                      dns=dns, cln=cln,
                      verbose=verbose)

    vims2isis(vims)
    spiceinit(vims)
    vimscal(vims)
    phocube(vims)
    noisefilter(vims)
    lowpass(vims)
