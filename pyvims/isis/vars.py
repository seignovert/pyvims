"""ISIS variables."""

BYTE_ORDERS = {
    'NoByteOrder': '=',  # system
    'Lsb': '<',          # little-endian
    'Msb': '>'           # big-endian
}

FIELD_TYPES = {
    'UnsignedByte': 'u1',
    'SignedByte': 'i1',
    'UnsignedWord': 'u2',
    'SignedWord': 'i2',
    'UnsignedInteger': 'u4',
    'SignedInteger': 'i4',
    'Integer': 'i4',
    'Real': 'f4',
    'Double': 'f8',
}
