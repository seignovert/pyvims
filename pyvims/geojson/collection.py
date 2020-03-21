"""Geojson feature collection module."""

from .geojson import GeoJson


class FeatureCollection(GeoJson):
    """Geojson feature collection object.

    Parameters
    ----------
    *features: list
        List of features.

    """

    def __init__(self, *features):
        self.features = features

    def __repr__(self):
        return f'<{self.__class__.__name__}> {len(self)} features'

    def __iter__(self):
        yield 'type', 'FeatureCollection'
        yield 'features', [dict(feature) for feature in self.features]

    def __len__(self):
        return len(self.features)

    def __getitem__(self, index):
        return self.features[index]
