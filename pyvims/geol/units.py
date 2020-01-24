"""Geological units module."""

import matplotlib.pyplot as plt

import numpy as np


def grid(img, lon_w, lat):
    """Convert geographic coordinates as image coordinates.

    Parameters
    ----------
    img: 2d-array
        2D geol map image centered at 180°.
    lon_w: float or array
        Point west longitude(s).
    lat: float or array
        Point latitude(s).

    Returns
    -------
    int or array, int or array
        Array closest coordinates on the image.

    """
    h, w = np.shape(img)

    if isinstance(lon_w, (list, tuple)):
        lon_w = np.asarray(lon_w)

    if isinstance(lat, (list, tuple)):
        lat = np.asarray(lat)

    i = np.round(-lon_w % 360 * w / 360).astype(int)
    j = np.round((90 - lat) * h / 180).astype(int)

    if isinstance(lon_w, (int, float)):
        if lon_w == 0:
            i = w
    else:
        i[lon_w == 0] = w

    return i, j


def geol_units(img, lon_w, lat, legend=None):
    """Get geological units based on (lon, lat) coordinates.

    Parameters
    ----------
    img: 2d-array
        2D geol map image centered at 180°.
    lon_w: float or array
        Point west longitude(s).
    lat: float or array
        Point latitude(s).
    legend: dict, optional
        Table to mapping geol units to values.

    Returns
    -------
    float, str or array
        Geological unit(s).

    """
    i, j = grid(img, lon_w, lat)
    units = img[j, i]

    if not isinstance(legend, dict):
        return units

    if np.ndim(units) == 0:
        return legend[units]

    geol = np.vectorize(legend.get)(units)

    if np.ma.is_masked(lon_w) or np.ma.is_masked(lat):
        mask = np.ma.getmask(lon_w) | np.ma.getmask(lat)
        return np.ma.array(geol, mask=mask)

    return geol


class GeolUnits(type):
    """Geological map units."""

    MAP = None
    LEGEND = None
    IMG = None

    def __str__(cls):
        return cls.__name__

    def __repr__(cls):
        return f'<{cls.__class__.__name__}> {cls}'

    def __call__(cls, *args, legend=True):
        """Get geological units form image."""
        if len(args) == 1:
            img = args[0]

            if not hasattr(img, 'lon'):
                raise AttributeError('Missing `lon` attribute in image.')

            if not hasattr(img, 'lat'):
                raise AttributeError('Missing `lat` attribute in image.')

            geol = cls.geol_units(img.lon, img.lat, legend=legend)

            return np.ma.array(geol, mask=img.limb) if hasattr(img, 'limb') else geol

        if len(args) == 2:
            lon, lat = args
            return cls.geol_units(lon, lat, legend=legend)

        raise TypeError('Takes anf IMAGE or LON and LAT value(s).')

    @property
    def img(cls):
        """Map image data."""
        if cls.IMG is None:
            cls.IMG = (plt.imread(str(cls.MAP)) * 255).astype(np.uint8)
        return cls.IMG

    def geol_units(cls, lon_w, lat, legend=True):
        """Get geological units.

        Parameters
        ----------
        lon_w: float or array
            Point west longitude(s).
        lat: float or array
            Point latitude(s).
        legend: dict, optional
            Table to mapping geol units to values.
            By default, the values are legend based
            on the map geological legend.

        Returns
        -------
        float, str or array
            Geological unit(s) or value(s) (if `legend` is set to `False`).

        """
        if legend and isinstance(legend, bool):
            legend = cls.LEGEND

        return geol_units(cls.img, lon_w, lat, legend=legend)

    def legend(cls, ax=None, legend=None, cmap=None, title='Units:', **kwargs):
        """Add legend caption."""
        if ax is None:
            ax = plt.gca()

        if legend is None:
            legend = cls.LEGEND

        for key, value in legend.items():
            ax.scatter([], [], color=plt.get_cmap(cmap)(key / 255), label=value)

        ax.legend(title=title, **kwargs)
