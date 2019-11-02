"""PDS times modules.

Cassini time are extracted from kernels:
    - ``naif0012.tls``
    - ``cas00171.tsc``

"""

import re
from datetime import datetime as dt

import numpy as np


CASSINI = np.transpose([
    # year, timestamp, cassini_time
    [1999, 915177600, 1293840277.05],
    [2000, 946713600, 1325376485.089],
    [2001, 978336000, 1356999098.185],
    [2002, 1009872000, 1388535319.111],
    [2003, 1041408000, 1420071542.054],
    [2004, 1072944000, 1451607752.163],
    [2005, 1104566400, 1483230358.172],
    [2006, 1136102400, 1514766561.229],
    [2007, 1167638400, 1546302762.211],
    [2008, 1199174400, 1577838967.232],
    [2009, 1230796800, 1609461592.044],
    [2010, 1262332800, 1640997816.03],
    [2011, 1293868800, 1672534037.122],
    [2012, 1325404800, 1704070236.234],
    [2013, 1357027200, 1735692838.148],
    [2014, 1388563200, 1767229038.233],
    [2015, 1420099200, 1798765239.134],
    [2016, 1451635200, 1830301441.106],
    [2017, 1483257600, 1861924044.223],
    [2018, 1514793600, 1893460247.199],
])


def dt_iso(time):
    """Parse ISO time pattern as datetime.

    Parameters
    ----------
    time: str
        Input string with time(s).

    Returns
    -------
    datetime.datetime or [datetime.datetime, …]
        Parsed time(s).

    Raises
    ------
    ValueError
        If the input time pattern is invalid.

    Examples
    --------
    >>> str(dt_iso('2005-02-14T18:02:29.123'))
    '2005-02-14 18:02:29.123000'

    >>> str(dt_iso('2005-02-14 18:02:29'))
    '2005-02-14 18:02:29'

    >>> str(dt_iso('2005-02-14:18:02'))
    '2005-02-14 18:02:00'

    >>> str(dt_iso('2005-02-14'))
    '2005-02-14 00:00:00'

    >>> dt_iso('from 2005-02-14T18:02:29 to 2005-02-14T18:03')
    [datetime.datetime(2005, 2, 14, 18, 2, 29), datetime.datetime(2005, 2, 14, 18, 3)]

    """
    times = re.findall(
        r'(\d{4})-(\d{2})-(\d{2})[T:\s]?(\d{2})?:?(\d{2})?:?(\d{2})?\.?(\d{1,6})?', time)

    if not times:
        raise ValueError(f'Invalid ISO datetime pattern `{time}`.')

    t = np.array([[int(_t) if _t != '' else 0 for _t in _time] for _time in times])

    # Convert millisecondes to microsecondes for datetime input.
    t[:, -1] = np.array([int(1e6 * float(f'0.{_t}')) for _t in t[:, -1]])

    return dt(*t[0]) if len(t) == 1 else [dt(*_t) for _t in t]


def dt_doy(time):
    """Parse DOY time pattern as datetime.

    Parameters
    ----------
    time: str
        Input string with time(s).

    Returns
    -------
    datetime.datetime or [datetime.datetime, …]
        Parsed time(s).

    Raises
    ------
    ValueError
        If the input time pattern is invalid.

    Examples
    --------
    >>> str(dt_doy('2005-045T18:02:29.123'))
    '2005-02-14 18:02:29.123000'

    >>> str(dt_doy('2005-045 18:02:29'))
    '2005-02-14 18:02:29'

    >>> str(dt_doy('2005-045:18:02'))
    '2005-02-14 18:02:00'

    >>> str(dt_doy('2005-045'))
    '2005-02-14 00:00:00'

    >>> dt_doy('from 2005-045T18:02:29 to 2005-045T18:03')
    [datetime.datetime(2005, 2, 14, 18, 2, 29), datetime.datetime(2005, 2, 14, 18, 3)]

    """
    times = re.findall(
        r'(\d{4})-(\d{3})[T:\s]?(\d{2})?:?(\d{2})?:?(\d{2})?\.?(\d{1,6})?', time)

    if not times:
        raise ValueError(f'Invalid DOY pattern `{time}`.')

    t = np.array([[int(_t) if _t != '' else 0 for _t in _time] for _time in times])

    # Convert millisecondes to microsecondes for datetime input.
    t[:, -1] = np.array([int(1e6 * float(f'0.{_t}')) for _t in t[:, -1]])

    # Reformat string for datetime parser.
    t = [dt.strptime(
        f'{_t[0]:04d}-{_t[1]:03d}T{_t[2]:02d}:{_t[3]:02d}:{_t[4]:02d}.{_t[5]:06d}',
        '%Y-%jT%H:%M:%S.%f') for _t in t]

    return t[0] if len(t) == 1 else t


def dt_date(time, eod=False):
    """Parse date pattern as datetime.

    Parameters
    ----------
    time: str
        Input string with time(s).
    eod: bool, optional
        End of the day (``23:59:59``).

    Returns
    -------
    datetime.datetime or [datetime.datetime, …]
        Parsed time(s).

    Raises
    ------
    ValueError
        If the input time pattern is invalid.

    Note
    ----
    If the date is prefix with ``through`` or ``to`` the
    end of day key will be triggered.

    Examples
    --------
    >>> str(dt_date('Feb 14, 2005'))
    '2005-02-14 00:00:00'

    >>> str(dt_date('Febr 14, 2005'))
    '2005-02-14 00:00:00'

    >>> str(dt_date('Feb 14, 2005', eod=True))
    '2005-02-14 23:59:59'

    >>> str(dt_date('to Feb 14, 2005'))
    '2005-02-14 23:59:59'

    >>> dt_date('from Feb 14, 2005 through March 12, 2006')
    [datetime.datetime(2005, 2, 14, 0, 0), datetime.datetime(2006, 3, 12, 23, 59, 59)]

    """
    times = re.findall(r'(through|to)?\s?([A-Z][a-z]{2})[a-z]*\s(\d+),\s(\d{4})', time)

    if not times:
        raise ValueError(f'Invalid date pattern `{time}`.')

    t = [dt.strptime(
        ' '.join([*_t[1:], '23:59:59' if eod or _t[0] != '' else '00:00:00']),
        '%b %d %Y %H:%M:%S') for _t in times]

    return t[0] if len(t) == 1 else t


def pds_time(time):
    """Parse PDS time.

    Parameters
    ----------
    time: str
        PDS time.

    Returns
    -------
    datetime.datetime
        Parsed time.

    Raises
    ------
    ValueError
        If the input time pattern is invalid.

    """
    try:
        return dt_iso(time)
    except ValueError:
        try:
            return dt_doy(time)
        except ValueError:
            try:
                return dt_date(time)
            except ValueError:
                raise ValueError(f'Invalid pattern `{time}`.')


def cassini_time(time):
    """Parse Cassini time.

    Parameters
    ----------
    time: str, int or float
        Cassini time.

    Returns
    -------
    float
        Parsed Cassini time as float.

    Raises
    ------
    ValueError
        If the input time pattern is invalid.

    Examples
    --------
    >>> cassini_time('v1487096932_1')
    1487096932.0

    >>> cassini_time(1483230358.172)
    1483230358.172

    """
    cassini_time = re.findall(r'(\d{10})(\.\d+)?', str(time))

    if not cassini_time:
        raise ValueError(f'Cassini time invalid: `{time}`')

    return float(''.join(cassini_time[0]))


def cassini2utc(time, decimals=0):
    """Convert Cassini time to UTC.

    Parameters
    ----------
    time: str, int or float
        Cassini time.
    decimals: int, optional
        Rounding decimal in time.

    Returns
    -------
    datetime.datetime
        UTC time.

    Examples
    --------
    >>> str(cassini2utc('v1487096932_1'))
    '2005-02-14 18:02:29'

    >>> str(cassini2utc(1483230358.172))
    '2005-01-01 00:00:00'

    """
    timestamp = np.interp(cassini_time(time), CASSINI[2], CASSINI[1])
    return dt.fromtimestamp(np.round(timestamp, decimals=decimals))


def utc2cassini(time):
    """Convert UTC to Cassini time.

    Parameters
    ----------
    time: str or datetime.datetime
        UTC time.
    decimals: int, optional
        Rounding decimal in time.

    Returns
    -------
    datetime.datetime
        UTC time.

    Raises
    ------
    ValueError
        If the input time pattern is invalid.

    Examples
    --------
    >>> utc2cassini('2005-02-14T18:02:29')
    1487096932.0...

    >>> utc2cassini('May 17, 2007 through Jun 30, 2007')
    array([1.55804964e+09, 1.56193766e+09])

    """
    t = pds_time(time)
    timestamp = [_t.timestamp() for _t in t] if isinstance(t, list) else t.timestamp()
    return np.interp(timestamp, CASSINI[1], CASSINI[2])
