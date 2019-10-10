"""Titan lakes module."""

import os

import numpy as np

from scipy import misc as im

from ..projections.sterographic import stereo_scale, xy as stereo_xy
from ..vars import ROOT_DATA


filename = 'titan_npole_lakes_radar_iss_stereo_60.png'
lat_min = 60
threshold = 128
n_pole = True
lakes = im.imread(os.path.join(ROOT_DATA, filename)) < threshold

center, scale = stereo_scale(lakes, lat_min, n_pole=n_pole)


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


def is_lake(lon, lat):
    """Convert geographic coordinates on the image.

    Parameters
    ----------
    lon: float
        Longitude West (degree).
    lat: float
        Latitude North (degree).

    Returns
    -------
    bool
        ``TRUE`` is the coordinates correspond to a lake.

    """
    x, y = np.clip(np.round(xy(lon, lat)).astype(np.int16), 0, int(2 * center))
    return lakes[y, x]
