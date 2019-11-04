"""Command Line module."""

import argparse
import os

from .releases import PDS

def cli(argv=None):
    """PDS command line interface entry point."""
    parser = argparse.ArgumentParser(description='Search data location on the PDS.')

    parser.add_argument('fname', nargs='+', help='Input file name(s).')
    parser.add_argument('-i', '--instrument', metavar='NAME',
                        default='VIMS', help='Instrument name.')
    parser.add_argument('-p', '--prefix',
                        default='co', help='Release prefix.')
    parser.add_argument('-s', '--src',
                        default='jpl', help='Release source.')
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update release list')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet output')

    argv = argv if argv is not None else os.sys.argv[1:]

    if not argv:
        parser.print_help(os.sys.stderr)
    else:
        args, others = parser.parse_known_args(argv)

        pds = PDS(args.instrument, prefix=args.prefix, src=args.src,
                  update=args.update, verbose=(not args.quiet))

        for name in args.fname:
            try:
                print(pds[name])
            except IndexError:
                print(f'File `{name}` is not available on the PDS.')
