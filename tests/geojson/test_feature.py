"""Test GeoJson feature module."""

from pyvims.geojson import FeatureCollection
from pyvims.geojson.feature import Feature


def test_feature():
    """Test GeoJson feature."""
    feature = Feature([30, 10])

    assert feature == (
        '{"type": "Feature", '
        '"geometry": {"type": "Point", "coordinates": [30, 10]}, '
        '"properties": {}'
        '}')

    assert dict(feature) == {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [30, 10],
        },
        'properties': {},
    }

    feature = Feature([30, 10], {'id': 123, 'name': 'foo'})

    assert feature == (
        '{"type": "Feature", '
        '"geometry": {"type": "Point", "coordinates": [30, 10]}, '
        '"properties": {"id": 123, "name": "foo"}'
        '}')

    assert dict(feature) == {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [30, 10],
        },
        'properties': {
            'id': 123,
            'name': 'foo',
        },
    }


def test_feature_add():
    """Test features addition to create collections."""
    feature = Feature([30, 10])

    coll = feature + feature
    assert isinstance(coll, FeatureCollection)
    assert len(coll) == 2
    assert coll[0] == feature
    assert coll[1] == feature

    coll = feature + feature + feature
    assert isinstance(coll, FeatureCollection)
    assert len(coll) == 3
    assert coll[0] == feature
    assert coll[1] == feature
    assert coll[2] == feature
