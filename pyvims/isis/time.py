"""Isis time parser."""

from datetime import datetime as dt


def time(t):
    """Parse string in datetime."""
    if isinstance(t, dt):
        return t

    if isinstance(t, str):
        return dt.strptime(t, '%Y-%jT%H:%m:%S.%f')

    raise TypeError(f'Time type `{t}` is invalid.')
