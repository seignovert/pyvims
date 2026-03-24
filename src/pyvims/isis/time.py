"""Isis time parser."""

import struct
import binascii
from datetime import datetime as dt


def time(t):
    """Parse string in datetime."""
    if isinstance(t, dt):
        return t

    if isinstance(t, str):
        return dt.strptime(t, '%Y-%jT%H:%M:%S.%f')

    raise TypeError(f'Time type `{t}` is invalid.')


def hex2double(s):
    """Convert Ephemeris Time hex string into double."""
    return struct.unpack('d', binascii.unhexlify(s))[0]
