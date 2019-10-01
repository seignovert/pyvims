"""VIMS wget module."""

import hashlib
import io
import os

import requests

from tqdm import tqdm


def nb_chunk(request, chunk=1024):
    '''Calculate the number of chunk of a request size.

    Parameters
    ----------
    content: int
        Request content length.
    chunk: int, optional
        Size of the chunks.

    Return
    -------
    int
        Number of chunks expected in the request.

    Examples
    --------
    >>> nb_chunk(1024)
    1
    >>> nb_chunk(1025)
    2
    >>> nb_chunk(2048)
    2
    >>> nb_chunk(2048, 100)
    21

    Note
    ----
    The VIMS data portal stream the binary content
    does not provide a ``content-length`` value.
    For now we get this value to ``4594223`` (4.4 Mb) which
    correspond to the size of a typical 64x64 IR cube.

    '''
    if 'content-length' in request.headers:
        size = int(request.headers['content-length'])
    else:
        size = 4594223
    return size // chunk + 1 if size % chunk != 0 else size // chunk


def wget(url, filename=None, md5=None, overwrite=False, verbose=True, chunk_size=1024):
    '''Download file based on url and it as file.

    Parameters
    ----------
    url: str
        URL of the file to download
    filename: str, optional
        Output filename.
    md5: str
        MD5 hash of the data.
    overwrite: bool, optional
        Enable file overwriting.
    verbose: bool, optional
        Toggle download verbose progress bar.
    chunk_size: int, optional
        Request iteration chunk size (bytes).

    Return
    -------

    Raises
    ------
    FileExistsError
        If the file already exists and :py:attr:`overwrite`
        is not set to ``True``.
    HTTPError
        If the HTTP request is invalid.

    '''
    # tqdm bar format
    bar_format = '{desc}: {percentage:3.0f}% |{bar}| ({rate_fmt}{postfix})'

    if filename is not None:
        if os.path.exists(filename) and not overwrite:
            raise FileExistsError(
                f'{filename} already exists. Add `overwrite=True` to overwrite it.')

        fname = os.path.basename(filename)
    else:
        fname = url.split('/')[-1]

    with requests.get(url, stream=True) as r:

        if r.status_code != requests.codes.ok:
            r.raise_for_status()

        with io.BytesIO() as b:
            for chunk in tqdm(r.iter_content(chunk_size),
                              total=nb_chunk(r, chunk_size),
                              desc=f"Download {fname}",
                              unit='B',
                              unit_divisor=chunk_size,
                              unit_scale=True,
                              miniters=1,
                              bar_format=bar_format,
                              disable=(not verbose),
                              leave=None):
                if chunk:
                    b.write(chunk)

            data = b.getvalue()

    check_md5(data, md5)

    if filename is not None:
        with open(filename, 'wb') as f:
            f.write(data)

    return data


def check_md5(data, md5=None):
    '''Check MD5 checksum matches the expeted value.

    Parameters
    ----------
    data: bytes
        Input data.
    md5: str, optional
        Expected MD5 string.

    Return
    ------
    bool
        ``True`` if match and ``False`` is :py:attr:`md5` is ``None``.

    Raises
    ------
    IOError
        If :py:attr:`md5` don't match.

    '''
    if md5 is not None:
        data_md5 = hashlib.md5(data).hexdigest()  # nosec: B303
        if data_md5 != md5:
            raise IOError(
                'MD5 data ({data_md5}) does not match the expected value ({md5}).')
        return True
    return False
