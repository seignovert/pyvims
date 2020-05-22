"""PDS times modules.

Cassini time are extracted from kernels:
    - ``naif0012.tls``
    - ``cas00171.tsc``

"""

import re
from datetime import datetime as dt, timezone as tz


import numpy as np


CASSINI = np.transpose([
    # year, timestamp, cassini_time
    [1999, 915148800, 1293840277.050],
    [2000, 946684800, 1325376485.089],
    [2001, 978307200, 1356999098.185],
    [2002, 1009843200, 1388535319.111],
    [2003, 1041379200, 1420071542.054],
    [2004, 1072915200, 1451607752.163],
    [2005, 1104537600, 1483230358.172],
    [2006, 1136073600, 1514766561.229],
    [2007, 1167609600, 1546302762.211],
    [2008, 1199145600, 1577838967.232],
    [2009, 1230768000, 1609461592.044],
    [2010, 1262304000, 1640997816.030],
    [2011, 1293840000, 1672534037.122],
    [2012, 1325376000, 1704070236.234],
    [2013, 1356998400, 1735692838.148],
    [2014, 1388534400, 1767229038.233],
    [2015, 1420070400, 1798765239.134],
    [2016, 1451606400, 1830301441.106],
    [2017, 1483228800, 1861924044.223],
    [2018, 1514764800, 1893460247.199],
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
    '2005-02-14 18:02:29.123000+00:00'

    >>> str(dt_iso('2005-02-14 18:02:29'))
    '2005-02-14 18:02:29+00:00'

    >>> str(dt_iso('2005-02-14:18:02'))
    '2005-02-14 18:02:00+00:00'

    >>> str(dt_iso('2005-02-14'))
    '2005-02-14 00:00:00+00:00'

    >>> dt_iso('from 2005-02-14T18:02:29 to 2005-02-14T18:03')
    [datetime.datetime(2005, 2, 14, 18, 2, 29, tzinfo=datetime.timezone.utc),
     datetime.datetime(2005, 2, 14, 18, 3, tzinfo=datetime.timezone.utc)]

    """
    times = re.findall(
        r'(\d{4})-(\d{2})-(\d{2})[T:\s]?(\d{2})?:?(\d{2})?:?(\d{2})?\.?(\d{1,6})?', time)

    if not times:
        raise ValueError(f'Invalid ISO datetime pattern `{time}`.')

    t = np.array([[int(_t) if _t != '' else 0 for _t in _time] for _time in times])

    # Convert millisecondes to microsecondes for datetime input.
    t[:, -1] = np.array([int(1e6 * float(f'0.{_t}')) for _t in t[:, -1]])

    return dt(*t[0], tzinfo=tz.utc) if len(t) == 1 else \
        [dt(*_t, tzinfo=tz.utc) for _t in t]


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
        f'{_t[0]:04d}-{_t[1]:03d}T{_t[2]:02d}:{_t[3]:02d}:{_t[4]:02d}.{_t[5]:06d}+0000',
        '%Y-%jT%H:%M:%S.%f%z') for _t in t]

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
        ' '.join([*_t[1:], '23:59:59' if eod or _t[0] != '' else '00:00:00']) + '+0000',
        '%b %d %Y %H:%M:%S%z') for _t in times]

    return t[0] if len(t) == 1 else t


def pds_folder(name):
    """Parse PDS folder name as string.

    Parameters
    ----------
    name: str
        Input older name.

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
    >>> pds_folder('2005015T175855')
    '2005-015T17:58:55'

    >>> pds_folder('2005015T175855_2005016T184233/')
    '2005-015T17:58:55 2005-016T18:42:33'

    """
    times = re.findall(r'(\d{4})(\d{3})T(\d{2})(\d{2})(\d{2})', name)

    if not times:
        return name

    return ' '.join([f'{_t[0]}-{_t[1]}T{_t[2]}:{_t[3]}:{_t[4]}' for _t in times])


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
    time = pds_folder(time)
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
    return dt.utcfromtimestamp(np.round(timestamp, decimals=decimals))


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


def dyear(time):
    """Convert datetime to decimal year.

    Parameters
    ----------
    time: str or datetime.datetime
        UTC time or date.

    Returns
    -------
    float
        Decimal year.

    Note
    ----
    The resolution is fixed at 1e-4 and take into account leap years.

    Examples
    --------
    >>> dyear('2005-01-01')
    2005.0
    >>> dyear('2005-12-31')
    2005.9973
    >>> dyear('2004-12-31')
    2004.9973

    """
    t = pds_time(str(time))
    frac = (float(t.strftime('%j')) - 1) / float(dt(t.year, 12, 31).strftime('%j'))
    return np.round(t.year + frac, 4)
