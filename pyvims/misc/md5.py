"""MD5 module."""

import hashlib
from pathlib import Path


def get_md5(data, string=False) -> str:
    """Get MD5 hash from data or a file.

    Parameters
    ----------
    data: str, bytes or Path
        Input file or data.
    sting: bool, optional
        By default. stings are considered as filenames.
        Set `string` argument to `True` to process strings
        directly.

    Returns
    -------
    string
        Hex digest MD5 string.

    Raises
    ------
    FileNotFoundError
        If a filename is provided but does not exists.

    """
    if isinstance(data, str):
        return get_md5(data.encode('utf-8')) if string else get_md5(Path(data))

    if isinstance(data, Path):
        if not data.exists():
            raise FileNotFoundError(data)

        return get_md5(data.read_bytes())

    return hashlib.md5(data).hexdigest()  # nosec: B303


def check_md5(data, md5: str) -> bool:
    """Check MD5 checksum matches the expeted value.

    Parameters
    ----------
    data: str, bytes or Path
        Input data or filename.
    md5: str
        Expected MD5 string.

    Returns
    -------
    bool
        `True` if expected and computed MD5 match.

    Raises
    ------
    IOError
        If MD5 don't match the computed MD5.

    Note
    ----
    If `data` is a string, it will be considered as a filename.

    """
    computed = get_md5(data)

    if computed == md5:
        return True

    raise IOError(f'MD5 data ({computed}) does not match '
                  f'the expected value ({md5}).')
