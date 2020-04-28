"""Test MD5 module."""

from pyvims.misc import check_md5, get_md5

from pathlib import Path

from pytest import raises


QUB = Path(__file__).parents[1] / 'data' / 'v1815243432_1.qub'
MD5 = '58a3ac2623d1d103e0077da1b0e56cf3'


def test_md5_file():
    """Test md5 with filename."""
    filename = str(QUB.absolute())
    assert get_md5(filename) == MD5
    assert check_md5(filename, MD5)


def test_md5_path():
    """Test md5 path object."""
    assert get_md5(QUB) == MD5
    assert check_md5(QUB, MD5)


def test_md5_data():
    """Test md5 on data."""
    data = QUB.read_bytes()
    assert get_md5(data) == MD5
    assert check_md5(data, MD5)


def test_md5_str():
    """Test md5 on strings."""
    assert get_md5('foo', string=True) == 'acbd18db4cc2f85cedef654fccc4a4d8'
    assert get_md5(b'foo') == 'acbd18db4cc2f85cedef654fccc4a4d8'
    assert check_md5(b'foo', 'acbd18db4cc2f85cedef654fccc4a4d8')


def test_md5_err():
    """Test md5 errors."""
    # Missing file
    with raises(FileNotFoundError):
        _ = get_md5('foo.py')

    # String is always a filename in check_md5
    with raises(FileNotFoundError):
        _ = check_md5('foo', 'acbd18db4cc2f85cedef654fccc4a4d8')

    # Invalid MD5
    with raises(IOError):
        _ = check_md5(QUB, 'bar')
