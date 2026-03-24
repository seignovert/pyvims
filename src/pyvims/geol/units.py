"""Geological units module."""

import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path

import numpy as np

from ..misc.vertices import path_gc_lonlat
from ..projections.equirectangular import pixel_area as equi_pixel_area
from ..projections.img import index


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
    units = img[index(img, lon_w, lat)]

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

    R = None       # Planet radius [km]
    MAP = None     # Geol map image
    LEGEND = None  # Units mapping dict

    EXTENT = [360, 0, -90, 90]  # Map extent
    NPT = 8                     # Great circle interpolation factor

    __img = None
    __lonlat = None
    __px_res = None

    def __str__(cls):
        return cls.__name__

    def __repr__(cls):
        return '\n - '.join([
            f'<{cls.__class__.__name__}> {cls} | Units:',
            *cls.LEGEND.values()
        ])

    def __call__(cls, *args, legend=True):
        """Get geological units form image."""
        if len(args) == 1:
            if hasattr(args[0], 'path'):
                return cls.pixel_frac(args[0], legend=legend)

            img = args[0]

            if not hasattr(img, 'lon'):
                raise AttributeError('Missing `lon` attribute in image.')

            if not hasattr(img, 'lat'):
                raise AttributeError('Missing `lat` attribute in image.')

            geol = cls.geol_units(img.lon, img.lat, legend=legend)

            if hasattr(img, 'limb') and np.ndim(img.limb) == 2:
                return np.ma.array(geol, mask=img.limb)

            return geol

        if len(args) == 2:
            lon, lat = args
            return cls.geol_units(lon, lat, legend=legend)

        raise TypeError('Takes anf IMAGE or LON and LAT value(s).')

    def __iter__(cls):
        return iter(cls.LEGEND.items())

    @property
    def img(cls):
        """Map image data."""
        if cls.__img is None:
            cls.__img = (plt.imread(str(cls.MAP)) * 255).astype(np.uint8)
        return cls.__img

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

    @property
    def shape(cls):
        """Image map shape."""
        return np.shape(cls.img)[:2]

    @property
    def lonlat(cls):
        """Map geographic coordinate grid."""
        if cls.__lonlat is None:
            h, w = cls.shape
            cls.__lonlat = np.meshgrid(
                np.linspace(0, 360, w)[::-1],
                np.linspace(-90, 90, h)[::-1],
                copy=False)
        return cls.__lonlat

    @property
    def pixel_area(cls):
        """Map pixel area."""
        if cls.__px_res is None:
            cls.__px_res = equi_pixel_area(cls.img, r=cls.R)
        return cls.__px_res

    @staticmethod
    def _get_path(pixel):
        """Get path from pixel."""
        if isinstance(pixel, Path):
            return pixel

        if hasattr(pixel, 'corners'):
            return pixel.corners.path

        if hasattr(pixel, 'path'):
            return pixel.path

        raise TypeError('Pixel must be a `Path` or have `corners` attribute.')

    def pixel_gc_path(cls, pixel):
        """Interpolate path edges on great circles."""
        return path_gc_lonlat(cls._get_path(pixel), npt=cls.NPT)

    def slice_img_path(cls, path):
        """Extract the portion of the image and the pixel area inside the path."""
        jmin, imin = index(cls.img, *np.max(path.vertices.T, axis=1))
        jmax, imax = index(cls.img, *np.min(path.vertices.T, axis=1))

        h, w = cls.shape
        cond = slice(jmin, min(h, jmax + 1)), slice(imin, min(w, imax + 1))

        _lon, _lat = cls.lonlat
        lon, lat = _lon[cond], _lat[cond]

        pts = np.transpose([lon.ravel(), lat.ravel()])
        inside = path.contains_points(pts).reshape(lon.shape)

        return cls.img[cond][inside], cls.pixel_area[cond][inside]

    def slice_img(cls, pixel):
        """Extract the portion of the image and the pixel area inside a pixel.

        Note
        ----
        * The pixel path edges on great circles.
        * The pixel path is splitted if it constrains multiple polygons before
        mergening the outputs.

        """
        path = cls.pixel_gc_path(pixel)
        verts = path.vertices
        codes = path.codes

        start = np.where(codes == Path.MOVETO)[0]
        stop = np.where(codes == Path.CLOSEPOLY)[0] + 1

        if len(start) != len(stop):
            raise ValueError('Path invalid.')

        if len(start) == 1:
            return cls.slice_img_path(path)

        # Loop through each individual path.
        pixel_units = []
        pixel_area = []
        for i, j in zip(start, stop):
            cond = slice(i, j)
            _path = Path(verts[cond], codes[cond])
            _pixel_units, _pixel_area = cls.slice_img_path(_path)
            pixel_units += list(_pixel_units)
            pixel_area += list(_pixel_area)

        return np.asarray(pixel_units), np.asarray(pixel_area)

    def pixel_frac(cls, pixel, legend=True):
        """Extract the portion of the image on the pixel."""
        pixel_units, pixel_area = cls.slice_img(pixel)
        total_area = np.sum(pixel_area)

        if legend and isinstance(legend, bool):
            legend = cls.LEGEND

        units = {}
        for key, name in legend.items():
            unit = pixel_units == key
            area = np.sum(pixel_area[unit])

            if area == 0:
                continue

            if name not in units:
                units[name] = 0

            units[name] += 100 * area / total_area

        return {k: v for k, v, in sorted(units.items(), key=lambda x: x[1], reverse=True)}

    def mask(cls, pixel, color='w', alpha=.9, reverse=False, **kwargs):
        """Create a hole mask patch of the pixel to put on top of the geol. map."""
        path = cls.pixel_gc_path(pixel)
        h, w = cls.shape

        bg = [
            [360, 90],
            [360, -90],
            [0, -90],
            [0, 90],
            [360, 90],
        ][::(-1 if reverse else 1)]

        vertices = bg + list(path.vertices)

        codes = [Path.MOVETO] + [Path.LINETO] * 3 + [Path.CLOSEPOLY] + list(path.codes)

        return PathPatch(Path(vertices, codes), color=color, alpha=alpha, ** kwargs)
