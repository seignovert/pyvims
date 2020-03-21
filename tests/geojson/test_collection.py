"""Test GeoJson feature collection module."""

from pyvims.geojson import Feature
from pyvims.geojson.collection import FeatureCollection

from pytest import fixture


@fixture
def feature():
    """Default feature."""
    return Feature([30, 10], {'id': 123, 'name': 'foo'})


def test_collection(feature):
    """Test GeoJson collection."""
    collection = FeatureCollection(feature)

    assert len(collection) == 1

    assert collection[0] == (
        '{"type": "Feature", '
        '"geometry": {"type": "Point", "coordinates": [30, 10]}, '
        '"properties": {"id": 123, "name": "foo"}'
        '}')

    assert dict(collection[0]) == {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [30, 10],
        },
        'properties': {
            'id': 123,
            'name': 'foo'
        },
    }

    assert collection == (
        '{"type": "FeatureCollection", '
        '"features": [{"type": "Feature", '
        '"geometry": {"type": "Point", "coordinates": [30, 10]}, '
        '"properties": {"id": 123, "name": "foo"}'
        '}]}')

    assert dict(collection) == {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [30, 10],
            },
            'properties': {
                'id': 123,
                'name': 'foo',
            },
        }],
    }

    # Two features
    collection = FeatureCollection(feature, feature)

    assert len(collection) == 2

    assert collection[1] == (
        '{"type": "Feature", '
        '"geometry": {"type": "Point", "coordinates": [30, 10]}, '
        '"properties": {"id": 123, "name": "foo"}'
        '}')

    assert collection == (
        '{"type": "FeatureCollection", '
        '"features": [{"type": "Feature", '
        '"geometry": {"type": "Point", "coordinates": [30, 10]}, '
        '"properties": {"id": 123, "name": "foo"}'
        '}, {"type": "Feature", '
        '"geometry": {"type": "Point", "coordinates": [30, 10]}, '
        '"properties": {"id": 123, "name": "foo"}'
        '}]}')

    assert dict(collection) == {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [30, 10],
            },
            'properties': {
                'id': 123,
                'name': 'foo',
            },
        }, {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [30, 10],
            },
            'properties': {
                'id': 123,
                'name': 'foo',
            },
        }],
    }
