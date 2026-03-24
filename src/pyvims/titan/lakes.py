"""Titan lakes module."""

import numpy as np

import matplotlib.pyplot as plt

from ..projections.stereographic import stereo_scale, xy as stereo_xy
from ..vars import ROOT_DATA


lat_min = 60
threshold = .5
n_pole = True


def _fname(name=None):
    """Lakes file based on lake name."""
    return f'titan_npole_stereo_60_{name}.png'


def _load_img(name):
    """Load lakes file."""
    return plt.imread(str(ROOT_DATA / _fname(name))) < threshold


lakes = {
    'all': _load_img('all_lakes'),
    'jingpo': _load_img('jingpo'),
    'kraken_inf': _load_img('kraken_inf'),
    'kraken_sup': _load_img('kraken_sup'),
    'kraken': _load_img('kraken_inf') | _load_img('kraken_sup'),
    'ligeia': _load_img('ligeia'),
    'punga_kivu': _load_img('punga_kivu'),
    'others': _load_img('other_lakes'),
}

center, scale = stereo_scale(lakes['all'], lat_min, n_pole=n_pole)


def xy(lon, lat):
    """Convert geographic coordinates on the image.

    Parameters
    ----------
    lon: float
        Longitude West (degree).
    lat: float
        Latitude North (degree).

    Returns
    -------
    float, float
        X-Y coordinates on the image.

    """
    return stereo_xy(lon, lat, center=(center, center), scale=scale, n_pole=n_pole)


def is_lake(lon, lat, name='all'):
    """Convert geographic coordinates on the image.

    Parameters
    ----------
    lon: float
        Longitude West (degree).
    lat: float
        Latitude North (degree).
    name:
        Lake name. Default ``all``.

    Returns
    -------
    bool
        ``TRUE`` is the coordinates correspond to a lake.

    """
    x, y = np.clip(np.round(xy(lon, lat)).astype(np.int16), 0, int(2 * center))
    return lakes[name.lower()][y, x]
