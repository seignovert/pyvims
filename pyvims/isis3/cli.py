# -*- coding: utf-8 -*-
import os
import argparse

from .vims import calibrate as vims_calibration

def cli_vims_calibration(argv=None):
    '''OPUS SETI API data entry point'''
    parser = argparse.ArgumentParser(description='Full VIMS calibration and denoise')
    parser.add_argument('imgID', help='VIMS cube ID')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet output')
    parser.add_argument('--qub', help='RAW data folder')
    parser.add_argument('--cub', help='ISIS CUB data folder')
    parser.add_argument('--nav', help='Navigation data folder')
    parser.add_argument('--cal', help='Calibrated data folder')
    parser.add_argument('--dns', help='Denoise data folder')
    parser.add_argument('--cln', help='Clean data folder')

    args, others = parser.parse_known_args(argv)

    imgID = args.imgID
    delattr(args, 'imgID')
    if args.qub is None:
        delattr(args, 'qub')
    if args.cub is None:
        delattr(args, 'cub')
    if args.cal is None:
        delattr(args, 'cal')
    if args.nav is None:
        delattr(args, 'nav')
    if args.dns is None:
        delattr(args, 'dns')
    if args.cln is None:
        delattr(args, 'cln')
    if args.quiet:
        setattr(args, 'verbose', False)
    else:
        setattr(args, 'verbose', True)
    delattr(args, 'quiet')

    return vims_calibration(imgID, **vars(args))

