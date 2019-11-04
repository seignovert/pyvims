"""Test PDS times modules."""

from pyvims.pds.times import (cassini2utc, cassini_time, dt_date, dt_doy, dt_iso,
                              pds_folder, pds_time, utc2cassini)


from pytest import approx, raises


def test_dt_iso():
    """Test parsing ISO time pattern."""
    assert str(dt_iso('2005-02-14T18:02:29.123')) == '2005-02-14 18:02:29.123000'
    assert str(dt_iso('2005-02-14 18:02:29')) == '2005-02-14 18:02:29'
    assert str(dt_iso('2005-02-14:18:02')) == '2005-02-14 18:02:00'
    assert str(dt_iso('2005-02-14')) == '2005-02-14 00:00:00'

    times = dt_iso('from 2005-02-14T18:02:29 to 2005-02-14T18:03')

    assert len(times) == 2
    assert str(times[0]) == '2005-02-14 18:02:29'
    assert str(times[1]) == '2005-02-14 18:03:00'

    with raises(ValueError):
        _ = dt_iso('2005-045')


def test_dt_doy():
    """Test parsing DOY time pattern."""
    assert str(dt_doy('2005-045T18:02:29.123')) == '2005-02-14 18:02:29.123000'
    assert str(dt_doy('2005-045 18:02:29')) == '2005-02-14 18:02:29'
    assert str(dt_doy('2005-045:18:02')) == '2005-02-14 18:02:00'
    assert str(dt_doy('2005-045')) == '2005-02-14 00:00:00'

    times = dt_doy('from 2005-045T18:02:29 to 2005-045T18:03')

    assert len(times) == 2
    assert str(times[0]) == '2005-02-14 18:02:29'
    assert str(times[1]) == '2005-02-14 18:03:00'

    with raises(ValueError):
        _ = dt_doy('2005-02-14')


def test_dt_date():
    """Test date pattern."""
    assert str(dt_date('Feb 14, 2005')) == '2005-02-14 00:00:00'
    assert str(dt_date('Febr 14, 2005')) == '2005-02-14 00:00:00'
    assert str(dt_date('Feb 14, 2005', eod=True)) == '2005-02-14 23:59:59'
    assert str(dt_date('to Feb 14, 2005')) == '2005-02-14 23:59:59'

    times = dt_date('from Feb 14, 2005 through March 12, 2006')

    assert len(times) == 2
    assert str(times[0]) == '2005-02-14 00:00:00'
    assert str(times[1]) == '2006-03-12 23:59:59'

    with raises(ValueError):
        _ = dt_date('2005-02-14')


def test_pds_time():
    """Test PDS time parsing."""
    assert str(pds_time('May 17, 2007')) == '2007-05-17 00:00:00'
    assert str(pds_time('2010-274T00:00:00')) == '2010-10-01 00:00:00'
    assert str(pds_time('2011-10-01T00:02:04.244')) == '2011-10-01 00:02:04.244000'

    t0, t1 = pds_time('… May 17, 2007 through Jun 30, 2007')
    assert str(t0) == '2007-05-17 00:00:00'
    assert str(t1) == '2007-06-30 23:59:59'

    t0, t1 = pds_time('… 2010-274T00:00:00 through 2010-365T23:59:59')
    assert str(t0) == '2010-10-01 00:00:00'
    assert str(t1) == '2010-12-31 23:59:59'

    t0, t1 = pds_time('… 2011-10-01T00:02:04.244 through 2011-12-31T12:28:45.128')
    assert str(t0) == '2011-10-01 00:02:04.244000'
    assert str(t1) == '2011-12-31 12:28:45.128000'

    t0, t1 = pds_time('2005015T175855_2005016T184233/')
    assert str(t0) == '2005-01-15 17:58:55'
    assert str(t1) == '2005-01-16 18:42:33'

    with raises(ValueError):
        _ = pds_time('No data available')


def test_cassini_time():
    """Test Cassini time parsing."""
    assert cassini_time('v1487096932_1') == 1487096932.0
    assert cassini_time(1483230358.172) == 1483230358.172

    with raises(ValueError):
        _ = cassini_time('v123_1')

    with raises(ValueError):
        _ = cassini_time(123)


def test_cassini2utc():
    """Test Cassini time to UTC converter."""
    assert str(cassini2utc('v1487096932_1')) == '2005-02-14 18:02:29'
    assert str(cassini2utc(1483230358.172)) == '2005-01-01 00:00:00'


def test_utc2cassini():
    """Test UTC to Cassini time converter."""
    assert utc2cassini('2005-02-14T18:02:29') == approx(1487096932.068, abs=1e-3)

    times = utc2cassini('May 17, 2007 through Jun 30, 2007')

    assert len(times) == 2
    assert times[0] == approx(1558049638.579, abs=1e-3)
    assert times[1] == approx(1561937662.855, abs=1e-3)


def test_pds_folder():
    """Test convert PDS folder as string."""
    assert pds_folder('2005015T175855') == '2005-015T17:58:55'
    assert pds_folder('2005015T175855_2005016T184233/') == \
        '2005-015T17:58:55 2005-016T18:42:33'
