"""Geojson feature module."""

from .collection import FeatureCollection
from .geojson import GeoJson
from .geometry import Geometry


class Feature(GeoJson):
    """Geojson feature object.

    Parameters
    ----------
    coordinates: list
        Feature coordinates.
    properties: dict
        Feature properties.

    """

    def __init__(self, coordinates, properties=None):
        self.geometry = Geometry(coordinates)
        self.properties = {} if properties is None else properties

    def __str__(self):
        return self.geometry.type

    def __iter__(self):
        yield 'type', 'Feature'
        yield 'geometry', dict(self.geometry)
        yield 'properties', self.properties

    def __add__(self, other):
        if isinstance(other, self.__class__):
            return FeatureCollection(self, other)

        if isinstance(other, FeatureCollection):
            return FeatureCollection(self, *other.features)

        raise TypeError(f'Need a {self.__class__} or a FeatureCollection object.')

    def __radd__(self, other):
        return self + other
