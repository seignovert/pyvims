"""Test GeoJson geometry module."""

from pathlib import Path

import numpy as np

from pyvims.geojson.geometry import Geometry

from pytest import raises


def test_geometry():
    """Test GeoJson geometry."""
    # Point
    geo = Geometry([30, 10])

    assert geo == '{"type": "Point", "coordinates": [30, 10]}'

    assert dict(geo) == {
        'type': 'Point',
        'coordinates': [30, 10],
    }

    # With numpy array
    geo = Geometry(np.array([30, 10]))

    assert geo == '{"type": "Point", "coordinates": [30, 10]}'

    # Line
    geo = Geometry([
        [30, 10], [10, 30], [40, 40]
    ])

    assert geo == (
        '{"type": "LineString", "coordinates": ['
        '[30, 10], [10, 30], [40, 40]'
        ']}')

    # Polygon
    geo = Geometry([
        [[30, 10], [40, 40], [20, 40], [10, 20], [30, 10]]
    ])

    assert geo == (
        '{"type": "Polygon", "coordinates": ['
        '[[30, 10], [40, 40], [20, 40], [10, 20], [30, 10]]'
        ']}')

    # Polygon with hole
    geo = Geometry([
        [[35, 10], [45, 45], [15, 40], [10, 20], [35, 10]],
        [[20, 30], [35, 35], [30, 20], [20, 30]]
    ])

    assert geo == (
        '{"type": "Polygon", "coordinates": ['
        '[[35, 10], [45, 45], [15, 40], [10, 20], [35, 10]], '
        '[[20, 30], [35, 35], [30, 20], [20, 30]]'
        ']}')


def test_geometry_err():
    """Test GeoJson geometry."""
    with raises(ValueError):
        _ = Geometry(30)

    with raises(ValueError):
        _ = Geometry([[[[30, 10]]]])


def test_geometry_save():
    """Test GeoJson geometry export."""
    geo = Geometry([30, 10])

    fout = Path('test.geojson')

    if fout.exists():
        fout.unlink()

    geo.save('test')

    assert fout.exists()

    assert fout.read_text() == \
        '{"type": "Point", "coordinates": [30, 10]}'

    with raises(FileExistsError):
        geo.save('test')

    geo.save('test.geojson', overwrite=True, verbose=False)

    fout.unlink()
    assert not fout.exists()
