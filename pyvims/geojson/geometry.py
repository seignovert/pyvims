"""Geojson geometry module."""

import numpy as np

from .geojson import GeoJson


class Geometry(GeoJson):
    """Geojson geometry object.

    Parameters
    ----------
    coordinates: list
        List of coordinates.

    """

    def __init__(self, coordinates):
        self.coordinates = coordinates

    def __str__(self):
        return self.type

    def __iter__(self):
        yield 'type', self.type
        yield 'coordinates', self.coordinates

    @property
    def coordinates(self):
        """Geometry coordinates."""
        return self.__coord

    @coordinates.setter
    def coordinates(self, values):
        """Coordinates setter.

        Raises
        ------
        ValueError
            If the collection dimension is invalid (<1 or >3)

        """
        coord = np.asarray(values)
        ndim = coord.ndim

        if ndim < 1:
            raise ValueError('Coordinates must have a dimension ≥ 1')
        if ndim > 3:
            raise ValueError('Coordinates must have a dimension <= 3')

        if ndim == 1 and coord.dtype.char != 'O':
            self.type = 'Point'
        elif ndim == 2:
            self.type = 'LineString'
        else:
            self.type = 'Polygon'

        self.__coord = coord.tolist()
