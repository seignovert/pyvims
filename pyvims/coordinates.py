"""Coordinates module."""

from .vectors import deg180, deg360


def slon(lon):
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
        return f'{-lon_e:.2f}°W' if isinstance(lon_e, float) else f'{-lon_e}°W'

    return f'{lon_e:.2f}°E' if isinstance(lon_e, float) else f'{lon_e}°E'


def slon_w(lon):
    """Longitude West string.


    Parameters
    ----------
    lon: float
        Input West longitude (degW).

    Returns
    -------
    str
        Formatter West longitude (`270°W|180°W|90°W|0°`)

    """
    lon_w = deg360(lon)

    if abs(lon_w) <= 1.e-2:
        return '0°'

    return f'{lon_w:.2f}°W' if isinstance(lon_w, float) else f'{lon_w}°W'


def slat(lat):
    """Latitude string.

    Parameters
    ----------
    lat: float
        Input latitude (degN).

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

    if lat > 0:
        return f'{lat:.2f}°N' if isinstance(lat, float) else f'{lat}°N'

    return f'{-lat:.2f}°S' if isinstance(lat, float) else f'{-lat}°S'


def salt(alt):
    """Altitude string (km)."""
    return f'{alt:.0f} km'
