"""Coordinates module."""

from .vectors import deg180


def slon(lon, precision=0):
    """Longitude string.

    Parameters
    ----------
    lon: float
        Input West longitude (degW).

    Returns
    -------
    str
        Formatter longitude (`180°|90°W|0°|90°E|180°|`)

    """
    lon_e = -deg180(lon)

    if abs(lon_e) <= 1.e-2:
        return '0°'

    if abs(deg180(lon_e - 180)) <= 1.e-2:
        return '180°'

    if lon_e < 0:
        return f'{-lon_e:.{precision}f}°W' if isinstance(lon_e, float) else f'{-lon_e}°W'

    return f'{lon_e:.{precision}f}°E' if isinstance(lon_e, float) else f'{lon_e}°E'


def slon_w(lon_w, precision=0):
    """West longitude string.

    Parameters
    ----------
    lon_w: float
        Input west longitude (degW).
    precision: int, optional
        Displayed float precision.

    Returns
    -------
    str
        Formatter West longitude (`360°W|270°W|180°W|90°W|0°`)

    """
    return '0°' if abs(lon_w) <= 1.e-2 else f'{lon_w:.{precision}f}°W'


def slon_e(lon_e, precision=0):
    """East longitude string.

    Parameters
    ----------
    lon_e: float
        Input east longitude (degE).
    precision: int, optional
        Displayed float precision.

    Returns
    -------
    str
        Formatter longitude (`180°|90°W|0°|90°E|180°|`)

    """
    return (f'{abs(lon_e):.{precision}f}°'
            f'{"" if abs(lon_e % 180) <= 1.e-2 else "E" if lon_e > 0 else "W"}')


def slat(lat, precision=0):
    """Latitude string.

    Parameters
    ----------
    lat: float
        Input latitude (degN).
    precision: int, optional
        Displayed float precision.

    Returns
    -------
    str
        Formatter latitude (`S.P.|45°S|Eq.|45°N|N.P.`)

    """
    if abs(lat) <= 1.e-2:
        return 'Eq.'

    if abs(lat - 90) <= 1.e-2:
        return 'N.P.'

    if abs(lat + 90) <= 1.e-2:
        return 'S.P.'

    return f'{abs(lat):.{precision}f}°{"N" if lat > 0 else "S"}'


def salt(alt):
    """Altitude string (km)."""
    return f'{alt:.0f} km'
