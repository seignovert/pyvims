"""Test wget module."""

from pyvims.wget import domain, wget_txt

from pytest import fixture, raises

from requests import HTTPError


@fixture
def html():
    """Mock HTML content."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Document</title>
</head>
<body>
    <h1>Title</h1>
    <p>
        Text with an external <a href="https://example.com/external.html">link</a>.
        and with an internal <a href="/internal.html">link</a>.
    </p>
</body>
</html>'''


def test_wget_domain():
    """Test domain from url."""

    assert domain('https://pds-imaging.jpl.nasa.gov/volumes/vims.html') == \
        'https://pds-imaging.jpl.nasa.gov/'
    assert domain('http://pds-imaging.jpl.nasa.gov/volumes/vims.html') == \
        'http://pds-imaging.jpl.nasa.gov/'
    assert domain('/pds-imaging.jpl.nasa.gov/volumes/vims.html') == \
        '/pds-imaging.jpl.nasa.gov/'

    with raises(ValueError):
        _ = domain('pds-imaging.jpl.nasa.gov/volumes/vims.html')

    with raises(ValueError):
        _ = domain('//pds-imaging.jpl.nasa.gov/')

    with raises(ValueError):
        _ = domain('http://pds-imaging.jpl.nasa.gov')


def test_wget_txt(requests_mock, html):
    '''Test wget text with requests.'''
    requests_mock.get('https://domain.tld/txt.html', text=html, status_code=200)

    txt = wget_txt('https://domain.tld/txt.html')

    assert 'Title' in txt
    assert '<a href="https://example.com/external.html">' in txt
    assert '<a href="https://domain.tld/internal.html">' in txt

    requests_mock.get('https://domain.tld/404-not-found', status_code=404)

    with raises(HTTPError):
        _ = wget_txt('https://domain.tld/404-not-found')
