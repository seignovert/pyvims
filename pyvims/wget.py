"""VIMS wget module."""

import io
import os
import re

import requests

from tqdm import tqdm

from .misc import check_md5


def nb_chunk(request, chunk=1024):
    """Calculate the number of chunk of a request size.

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

    """
    if 'content-length' in request.headers:
        size = int(request.headers['content-length'])
    else:
        size = 4594223
    return size // chunk + 1 if size % chunk != 0 else size // chunk


def wget(url, filename=None, md5=None, overwrite=False, verbose=True, chunk_size=1024):
    """Download file based on url and it as file.

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

    """
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

    if md5 is not None:
        check_md5(data, md5)

    if filename is not None:
        with open(filename, 'wb') as f:
            f.write(data)

    return data


def wget_txt(url):
    """Get web page text content.

    Parameters
    ----------
    url: str
        URL page to download.

    Raises
    ------
    HTTPError
        If the HTTP request is invalid.

    """
    resp = requests.get(url)
    if resp.status_code == requests.codes.ok:
        return resp.text.replace('href="/', f'href="{domain(url)}')
    return resp.raise_for_status()


def domain(url):
    """Get domain from url.

    Domain must start with ``http://``, ``https://``
    or ``/``.

    Parameters
    ----------
    url: str
        URL to parse to extract the domain.

    Raises
    ------
    ValueError
        If the URL pattern is invalid.

    Examples
    --------
    >>> domain('https://example.com/test/page.html')
    'https://example.com/'
    >>> domain('http://example.com/test/page.html')
    'http://example.com/'
    >>> domain('/example.com/test/page.html')
    '/example.com/'


    """
    pattern = re.compile(r'^(https?:/)?(/[a-z0-9][a-z0-9-_.]*/)')
    res = pattern.match(url)
    if res:
        return res.group(2) if res.group(1) is None else ''.join(res.groups())

    raise ValueError(f'Invalid URL pattern: `{url}`.')


def url_exists(url):
    """Check if the URL exists."""
    resp = requests.head(url)
    if resp.status_code == requests.codes.found:
        return url_exists(resp.headers['Location'])
    return resp.status_code == requests.codes.ok
