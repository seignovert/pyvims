"""Background maps module."""

import os
import re

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.image import imread
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection

from .vertices import path_lonlat
from ..projections.stereographic import r_stereo, xy as xy_stereo
from ..vars import ROOT_DATA
from ..vectors import deg180, deg360
from ..coordinates import slat, slon_e, slon_w


ROOT = ROOT_DATA / 'maps'


def parse(rexp, line):
    r"""Parse README line.

    Parameters
    ----------
    rexp: str
        Regular expression for parser.
    line: str
        Line to parse.

    Returns
    -------
    array
        Parsed value(s).

    Raises
    ------
    ValueError
        If not match was found.

    Example
    -------
    >>> parse(r'\d+', 'abc12def45')
    ['12', '45']

    """
    res = re.findall(rexp, line)
    if not res:
        raise ValueError(f'Invalid line: {line}')
    return res


def add(maps, keys, attr, value):
    """Add value(s) to maps dict.

    Parameters
    ----------
    maps: dict
        Global list of maps.
    keys: list
        List of file maps to append.
    attr: str
        Key value.
    value: any
        Value to append. If the value is a tuple, the values
        will loop according to ``keys`` index.

    Raises
    ------
    ValueError
        If the keys variable is ``None``.

    """
    if keys is None:
        raise ValueError('No map key(s) selected.')

    if isinstance(value, str) and value == 'None':
        return

    for i, key in enumerate(keys):
        if key not in maps.keys():
            maps[key] = {}
        maps[key][attr] = value[i] if isinstance(value, tuple) else value


def basename(fname):
    """Extract filename basename without extension.

    Parameters
    ----------
    fname: str
        Input filename

    Returns
    -------
    str
        File basename without extension.

    Example
    -------
    >>> basename('foo')
    'foo'
    >>> basename('foo.txt')
    'foo'
    >>> basename('test.foo.txt')
    'test.foo'
    >>> basename('test/foo.txt')
    'foo'
    >>> basename('/test/foo.txt')
    'foo'

    """
    return str(fname) if '.' not in str(fname) else \
        '.'.join(os.path.basename(str(fname)).split('.')[:-1])


def parse_readme(filename):
    """Parse README file.

    Parameters
    ----------
    filename: str
        README filename.

    Returns
    -------
    dict
        List of all the maps available in the README.

    """
    with open(filename, 'r') as f:
        lines = f.read().splitlines()

    maps = {}
    name = None
    keys = None
    for line in lines:
        if line.startswith('##'):
            name = line[2:].strip()
            keys = None

        elif line.startswith('* Filename:'):
            filenames = parse(r'`([\w\.\-\s/\\]+)`', line)

            files = tuple([os.path.basename(fname) for fname in filenames])
            roots = tuple([os.path.dirname(fname) for fname in filenames])

            keys = tuple([basename(f) for f in files])

            add(maps, keys, 'fname', files)
            add(maps, keys, 'root', roots)
            add(maps, keys, 'name', name)

        elif line.startswith('* Source:'):
            src, url = parse(r'\[([\w\.\-\s]*)\]\(([\w\.\-\s:/]*)\)', line)[0]

            add(maps, keys, 'src', src)
            add(maps, keys, 'url', url)

        elif line.startswith('* Extent:'):
            lon_1, lon_2, lat_1, lat_2 = parse(r'(-?\d+\.\d+|-?\d+)', line)
            extent = [float(lon_1), float(lon_2), float(lat_1), float(lat_2)]
            add(maps, keys, 'extent', extent)

        elif line.startswith('* Projection:'):
            projection = parse(r'`([\w\-_\s]+)`', line)[0]
            add(maps, keys, 'projection', projection.lower())

    return maps


def remove_from_readme(filename, fname):
    """Remove map from README file.

    Parameters
    ----------
    filename: str
        README filename.
    fname: str
        Filename to remove

    Returns
    -------
    dict
        List of all the maps available in the README.

    """
    with open(filename, 'r') as f:
        lines = f.read().splitlines()

    new = []
    buffer = []
    include = True
    for i, line in enumerate(lines):
        if line.startswith('##'):
            if buffer:
                new += buffer

            include = True
            buffer = []

        elif line.startswith('* Filename:'):
            filenames = parse(r'`([\w\.\-\s/\\]+)`', line)

            files = tuple([basename(fname) for fname in filenames])

            if fname in files:
                include = False
                buffer = []

        if include:
            buffer.append(line)

    if buffer:
        new += buffer

    with open(filename, 'w') as f:
        f.write('\n'.join(new))


class MapsDetails(type):
    """Map details parser."""

    __maps = {}

    def __repr__(cls):
        return '\n - '.join([
            f'<{cls.__name__}> Available: {len(cls)}',
            *cls.maps().keys()
        ])

    def __len__(cls):
        return len(cls.maps())

    def __contains__(cls, item):
        return item in cls.maps().keys()

    def __iter__(cls):
        return iter(cls.maps())

    def __getitem__(cls, item):
        try:
            return Map(**cls.maps()[item])
        except KeyError:
            raise KeyError(f'Unknown map `{item}`.')

    @classmethod
    def maps(cls):
        """Load all maps listed in content."""
        if not cls.__maps:
            cls.__maps = parse_readme(cls.filename())
        return cls.__maps

    @classmethod
    def filename(cls):
        """Get README filename.

        Raises
        ------
        FileNotFoundError
            If the file is missing.

        """
        filename = ROOT / 'README.md'

        if not filename.exists():
            with filename.open('w') as f:
                f.write('\n'.join([
                    'List of maps available',
                    '======================\n',
                    '## Titan VIMS/ISS\n',
                    '* Filename: `Titan_VIMS_ISS.jpg`',
                    '* Source: [Seignovert et al. 2019]'
                    '(https://doi.org/10.22002/D1.1173)',
                    '* Extent: `-180° 180° -90° 90°`',
                    '* Projection: `equirectangular`\n',
                ]))

        return str(filename)

    @classmethod
    def register(cls, m, update=False):
        """Register a new maps in README.

        Parameters
        ----------
        m: Map
            Background map object.
        update: bool, optional
            Enable map update with the same key.

        Raises
        ------
        TypeError
            If the map provided doest not have a
            ``markdown`` attribute.
        ValueError
            If the ``name`` attribute is already used.

        """
        if not hasattr(m, 'markdown'):
            raise TypeError(f'Map has an invalid type: `{type(m)}`.')

        key = basename(m)

        if key in cls.maps().keys():
            if update:
                cls.remove(key)
            else:
                raise ValueError(f'A map is already registered with the name: `{key}`.')

        with open(cls.filename(), 'a') as f:
            f.write(f'\n{m.markdown}')

        cls.__maps[key] = dict(m)

        print(f'Image `{key}` saved in MAPS registry.')

    @classmethod
    def remove(cls, fname):
        """Remove a map file from README."""
        key = basename(fname)

        if key in cls.maps().keys():
            remove_from_readme(cls.filename(), key)
            del cls.__maps[key]

            print(f'Image `{key}` removed from MAPS registry.')

    @classmethod
    def reload(cls):
        """Reload maps list from README."""
        cls.__maps = {}


class MAPS(metaclass=MapsDetails):
    """List of all the registered maps."""


class Map:
    """Background map object.

    Image filename format:

        `ROOT`/`Target`_`INSTR`.`ext`

    Parameters
    ----------
    fname: str
        Image filename.
    root: str, optional
        Data root folder containing the map.
        If ``None`` is provided (default), the
        package ``maps`` folder will be used.
    extent: list, required
        Map extent: [lon_w_0, lon_w_1, lat_1, lat_2]
    src: str, optional
        Image source name.
    url: str, optional
        Image URL source.
    projection:
        Image projection (default: ``equirectangular``).
    name: str, optional
        Name of the map (for the registry).

    """

    def __init__(self, fname, root=None, extent=None, src=None, url=None,
                 projection=None, name=None):
        self.root = root if root else str(ROOT)
        self.fname = fname

        self.data_extent = list(extent)
        self.src = src
        self.url = url
        self.proj = projection.lower() if isinstance(projection, str) else None

        self.name = name if name is not None else \
            '.'.join(self.fname.split('.')[:-1])

    def __str__(self):
        return self.fname if self.root == str(ROOT) else self.filename

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> {self}',
            f'Extent: {"Undefined" if self.data_extent is None else self.data_extent}',
            f'Source: {"Undefined" if self.src is None else self.src}',
            f'URL: {"Undefined" if self.url is None else self.url}',
            f'Projection: {"Undefined" if self.proj is None else self.proj.title()}',
        ])

    def __iter__(self):
        for k, v in self.as_dict.items():
            yield k, v

    def __call__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], PatchCollection):
                return self.xy_collection(args[0])

            if isinstance(args[0], PathPatch):
                return self.xy_patch(args[0])

            if isinstance(args[0], Path):
                return self.xy_path(args[0])

        if len(args) == 2:
            return self.xy(args[0], args[1])

        raise ValueError('A `PatchCollection`, `PathPatch`, `Patch` '
                         'or (lon_w, lat) attributes are required.')

    @property
    def fname(self):
        return self.__fname

    @fname.setter
    def fname(self, fname):
        if os.path.dirname(fname):
            self.root = os.path.dirname(fname)

        self.__fname = os.path.basename(fname)
        self.__img = None
        self.__n_pole = None

        if not os.path.exists(self.filename):
            raise FileNotFoundError(f'Map `{self.filename}` is not available.')

    @property
    def filename(self):
        """Image absolute path."""
        return os.path.join(self.root, self.fname)

    @property
    def extent_str(self):
        """Format data extent as string."""
        return ' '.join([f'{e}°' for e in self.data_extent])

    @property
    def markdown(self):
        """Convert Map object into markdown."""
        return '\n'.join([
            f'## {self.name}\n',
            f'* Filename: `{self}`',
            f'* Source: [{self.src}]({self.url})',
            f'* Extent: `{self.extent_str}`',
            f'* Projection: `{self.proj}`',
            f'\n![{self.name}]({self.filename})',
        ])

    @property
    def as_dict(self):
        """Convert as dict."""
        return {
            'name': self.name,
            'fname': self.fname,
            'root': self.root,
            'src': self.src,
            'url': self.url,
            'extent': self.data_extent,
            'projection': self.proj,
        }

    def register(self, update=False):
        """Register map in MAPS."""
        MAPS.register(self, update=update)

    @property
    def img(self):
        """Image data."""
        if self.__img is None:
            self.__img = imread(self.filename)
        return self.__img

    @property
    def shape(self):
        """Background image shape."""
        return self.img.shape

    @property
    def ndim(self):
        """Background image dimension."""
        return self.img.ndim

    @property
    def center_0(self):
        """Center equirectangular image background at 0°."""
        if self._proj != 'lonlat':
            raise ValueError('Recentering is only available for equirectangular maps.')

        if self.data_extent[0] == -180 and self.data_extent[1] == 180:
            return self

        if self.data_extent[0] != 360 or self.data_extent[1] != 0:
            raise ValueError('Longitude span invalid. Must be [360, 0], not '
                             f'[{self.data_extent[0]:.1f}, {self.data_extent[1]:.1f}].')

        if self.ndim == 2:
            _, ns = self.shape
            self.__img = np.hstack([self.img[:, ns // 2:], self.img[:, :ns // 2]])
        elif self.ndim == 3:
            _, ns, _ = self.shape
            self.__img = np.hstack([self.img[:, ns // 2:, :], self.img[:, :ns // 2, :]])
        else:
            raise ValueError(f'Image dimension invalid: {self.ndim}.')

        self.data_extent[:2] = [-180, 180]
        return self

    @property
    def center_180(self):
        """Center equirectangular image background at 180°."""
        if self._proj != 'lonlat':
            raise ValueError('Recentering is only available for equirectangular maps.')

        if self.data_extent[0] == 360 and self.data_extent[1] == 0:
            return self

        if self.data_extent[0] != -180 or self.data_extent[1] != 180:
            raise ValueError('Longitude span invalid. Must be [-180, 180], not '
                             f'[{self.data_extent[0]:.1f}, {self.data_extent[1]:.1f}].')

        if self.ndim == 2:
            _, ns = self.shape
            self.__img = np.hstack([self.img[:, ns // 2:], self.img[:, :ns // 2]])
        elif self.ndim == 3:
            _, ns, _ = self.shape
            self.__img = np.hstack([self.img[:, ns // 2:, :], self.img[:, :ns // 2, :]])
        else:
            raise ValueError(f'Image dimension invalid: {self.ndim}.')

        self.data_extent[:2] = [360, 0]
        return self

    @property
    def n_pole(self):
        """Pole observered for polar projection."""
        if self.__n_pole is None:
            if self._proj == 'stereo':
                self.__n_pole = self.data_extent[3] > 0
        return self.__n_pole

    @property
    def xright(self):
        """Check if x-axis is positive to the right."""
        return self.data_extent[1] < 0

    @property
    def _proj(self):
        if self.proj in [None, 'equi', 'equirectangular', 'plate carrée', 'lonlat']:
            return 'lonlat'

        if self.proj in ['stereo', 'stereographic']:
            return 'stereo'

        raise ValueError(f'Projection `{self.proj}` is not available.')

    @property
    def extent(self):
        """Projected data extent."""
        if self._proj in ['lon_w_lat', 'lon_e_lat']:
            return self.data_extent

        if self._proj == 'stereo':
            r = r_stereo(self.data_extent[2], n_pole=self.n_pole)
            return [-r, r, r, -r]

        return self.data_extent

    def xy(self, lon_w, lat):
        """Convert point coordinate in map coordinates.

        Parameters
        ----------
        lon_w: float
            Point longitude West (degree).
        lat: float
            Point latitude (degree).

        Returns
        -------
        float, float
            X-Y coordinates of the point on the surface.

        """
        if self._proj == 'lonlat':
            return deg180(np.asarray(lon_w)) if self.xright else deg360(lon_w), lat

        if self._proj == 'stereo':
            return xy_stereo(lon_w, lat, n_pole=self.n_pole)

        return self.data_extent

    def xy_path(self, path):
        """Convert path vertices in map coordinates.

        Parameters
        ----------
        path: matplotlib.path.Path
            Pyplot path.

        Returns
        -------
        matplotlib.path.Path
            Re-projected path.

        """
        if path is None:
            return None

        vertices = np.transpose(self.xy(*path.vertices.T))

        _path = Path(vertices, path.codes)

        if self._proj == 'lonlat':
            _path = path_lonlat(_path)

        return _path

    def xy_patch(self, patch):
        """Convert patch vertices in map coordinates.

        Parameters
        ----------
        patch: matplotlib.patches.PathPatch
            Pyplot patch.

        Returns
        -------
        matplotlib.patches.PathPatch
            Re-projected patch.

        """
        return PathPatch(
            self.xy_path(patch.get_path()),
            edgecolor=patch.get_ec(),
            facecolor=patch.get_fc(),
        )

    def xy_collection(self, collection):
        """Convert patch collection vertices in map coordinates.

        Parameters
        ----------
        collection: matplotlib.collections.PatchCollection
            Pyplot patch collection.

        Returns
        -------
        matplotlib.collections.PatchCollection
            Re-projected patch collection.

        """
        return PatchCollection(
            [
                PathPatch(self.xy_path(path))
                for path in collection.get_paths()
            ],
            edgecolor=collection.get_ec(),
            facecolor=collection.get_fc(),
        )

    def lons(self, lon_min=None, lon_max=None, npts=None):
        """Get longitude ticks.

        Parameters
        ----------
        lon_min: float, optional
            Minimal longitude. Use ``data_extent`` min value
            if ``None`` provided.
        lon_max: float, optional
            Minimal longitude. Use ``data_extent`` max value
            if ``None`` provided.
        npts: int, optional
            Number of points to output (default ``13``).

        Returns
        -------
        numpy.array
            List of longitudes.

        """
        if self._proj == 'stereo':
            return [0]

        lons = np.linspace(
            min(self.data_extent[:2]) if lon_min is None else lon_min,
            max(self.data_extent[:2]) if lon_max is None else lon_max,
            13 if npts is None else npts,
        )

        if self.data_extent[1] < 0:
            lons = lons[::-1]  # Revert x-axis

        return lons

    def lats(self, lat_min=None, lat_max=None, npts=None):
        """Get latitude ticks.

        Parameters
        ----------
        lat_min: float, optional
            Minimal latitude. Use ``data_extent`` min value
            if ``None`` provided.
        lat_max: float, optional
            Minimal latitude. Use ``data_extent`` max value
            if ``None`` provided.
        npts: int, optional
            Number of points to output (default ``7``).

        Returns
        -------
        numpy.array
            List of latitudes.

        """
        if self._proj == 'stereo':
            return [0]

        return np.linspace(
            min(self.data_extent[2:]) if lat_min is None else lat_min,
            max(self.data_extent[2:]) if lat_max is None else lat_max,
            7 if npts is None else npts,
        )

    def lonlabels(self, lon_min=None, lon_max=None, npts=None, precision=0):
        """Get longitude labels.

        Parameters
        ----------
        lon_min: float, optional
            Minimal longitude. Use ``data_extent`` min value
            if ``None`` provided.
        lon_max: float, optional
            Minimal longitude. Use ``data_extent`` max value
            if ``None`` provided.
        npts: int, optional
            Number of points to output (default ``13``).
        precision: int, optional
            Displayed float precision.

        Returns
        -------
        numpy.array
            List of longitude labels.

        """
        if self._proj == 'stereo':
            return [slon_w(0)]

        lons = self.lons(lon_min=lon_min, lon_max=lon_max, npts=npts)

        if self.data_extent[1] < 0:  # East longitude
            labels = [slon_e(-lon) for lon in lons]
        else:
            labels = [slon_w(lon) for lon in lons]

        return labels

    def latlabels(self, lat_min=None, lat_max=None, npts=None, precision=0):
        """Get latitude labels.

        Parameters
        ----------
        lat_min: float, optional
            Minimal latitude. Use ``data_extent`` min value
            if ``None`` provided.
        lat_max: float, optional
            Minimal latitude. Use ``data_extent`` max value
            if ``None`` provided.
        npts: int, optional
            Number of points to output (default ``13``).
        precision: int, optional
            Displayed float precision.

        Returns
        -------
        numpy.array
            List of latitude labels.

        """
        if self._proj == 'stereo':
            return [slon_w(90) if self.n_pole else slon_w(270)]

        lats = self.lats(lat_min=lat_min, lat_max=lat_max, npts=npts)

        return [slat(lat, precision) for lat in lats]

    @property
    def xlim(self):
        """X-axis limits based on image background."""
        return self.extent[0], self.extent[1]

    @property
    def ylim(self):
        """Y-axis limits based on image background."""
        return self.extent[2], self.extent[3]

    @staticmethod
    def paralleles(lat, nlons=181, lon_min=0, lon_max=360):
        """Paralleles coordinates.

        Parameters
        ----------
        lats: int, float or list
            Parallele latitude(s).
        nlons: int, optional
            Number of west longitudes in the parallele(s).
        lon_min: float, optional
            Minimum west longitude.
        lon_max: float, optional
            Maximum west longitude.

        Returns
        -------
        ([float, …], [float, …]) or [[float, float], …]
            West longitude and latitude of the parallele.

        """
        lons = np.linspace(lon_min, lon_max, nlons)
        lats = np.repeat(lat, nlons)

        if isinstance(lat, (list, np.ndarray)):
            nlats = len(lat)
            lats = np.repeat(lat, nlons).reshape(nlats, nlons).T
            lons = np.repeat(lons, nlats).reshape(nlons, nlats)

        return lons, lats

    @staticmethod
    def meridians(lon, nlats=91, lat_min=-90, lat_max=90):
        """Meridian coordinates.

        Parameters
        ----------
        lons: int, float or list
            Meridian longitude(s).
        nlats: int, optional
            Number of latitudes in the meridian(s).
        lat_min: float, optional
            Minimum latitude.
        lat_max: float, optional
            Maximum latitude.

        Returns
        -------
        ([float, …], [float, …]) or [[float, float], …]
            West longitude and latitude of the parallele.

        """
        lats = np.linspace(lat_min, lat_max, nlats)
        lons = np.repeat(lon, nlats)

        if isinstance(lon, (list, np.ndarray)):
            nlons = len(lon)
            lons = np.repeat(lon, nlats).reshape(nlons, nlats).T
            lats = np.repeat(lats, nlons).reshape(nlats, nlons)

        return lons, lats

    def subplots(self, *args, bgshow=True, ticks=True,
                 lim=True, grid=True, **kwargs):
        """Create subplots based on map background."""
        fig, ax = plt.subplots(*args, **kwargs)

        return fig, MapAxes(self, ax, bgshow=bgshow, ticks=ticks,
                            lim=lim, grid=grid)

    def figure(self, *args, **kwargs):
        """Create figure based on map background."""
        return self.subplots(*args, **kwargs)


class MapAxis:
    """Map axis object.

    Parameters
    ----------
    bg: Map
        Background Map object.
    ax: matplotlib.axes._subplots.AxesSubplot
        Matplotlib axis.
    bgshow: bool, optional
        Show basemap image (default: ``True``).
    ticks: bool, optional
        Show map X-Y ticks (default: ``True``).
    lim: bool, optional
        Set X-Y limits based on map extent (default: ``True``).
    grid: bool, optional
        Show default image grid (default: ``True``).

    """

    def __init__(self, bg, ax, bgshow=True, ticks=True,
                 lim=True, grid=True):
        self.bg = bg
        self.ax = ax

        if bgshow:
            self.set_bg()
        if ticks:
            self.set_xyticks()
            self.set_xyticklabels()
        if lim:
            self.set_xylim()
        if grid:
            self.grid()

    def __repr__(self):
        return f'<{self.__class__.__name__}> {self.bg}'

    def set_bg(self, cmap='gray', **kwargs):
        """Show background image scaled on the map."""
        self.ax.imshow(self.bg.img, extent=self.bg.extent, cmap=cmap, **kwargs)

    def set_xyticks(self, xticks=None, yticks=None):
        """Set axis X-Y ticks."""
        self.ax.set_xticks(self.bg.lons() if xticks is None else xticks)
        self.ax.set_yticks(self.bg.lats() if yticks is None else yticks)

    def set_xyticklabels(self, lats=[60, 70, 80], lon_w=45,
                         color='lightgray',
                         xticklabels=None, yticklabels=None):
        """Set axis X-Y ticklabels.

        Parameters
        ----------
        lats: list, optional
            Latitudes to display meridian values.
        lon_w: float, optional
            West longitude to display meridian values.

        """
        self.ax.set_xticklabels(
            self.bg.lonlabels() if xticklabels is None else xticklabels)
        self.ax.set_yticklabels(
            self.bg.latlabels() if yticklabels is None else yticklabels)

        if (self.bg._proj == 'stereo'
                and yticklabels is None
                and yticklabels is None):
            for lat in lats:
                self.ax.text(*self.bg(lon_w, lat), slat(lat),
                             rotation=-lon_w, color=color,
                             va='baseline', ha='center')

    def set_xylim(self, bl_lon_w=None, bl_lat=None, tr_lon_w=None, tr_lat=None):
        """Set X-Y axis limits based on map dimensions."""
        if None in [bl_lon_w, bl_lat, tr_lon_w, tr_lat]:
            self.ax.set_xlim(self.bg.xlim)
            self.ax.set_ylim(self.bg.ylim)
        else:
            xmin, ymin = self.bg(bl_lon_w, bl_lat)
            xmax, ymax = self.bg(tr_lon_w, tr_lat)
            self.ax.set_xlim(xmin, xmax)
            self.ax.set_ylim(ymin, ymax)

    def grid(self, lats=[60, 70, 80], lons=[30, 60, 120, 150, 210, 240, 310, 340],
             lat_min=60, lat_max=80, nlats=21,
             color='lightgray', lw=.5, **kwargs):
        """Set image ticks, limits and grid.

        Parameters
        ----------
        lats: list, optional
            List of parallele latitudes in stereographic projection.
        lons: list, optional
            List of meridians west longitudes in stereographic projection.
        lat_min: float, optional
            Minimum meridian latitude in stereographic projection.
        lat_max: float, optional
            Maximum meridian latitude in stereographic projection.
        nlats: int, optional
            Number of latitudes points per meridians in stereographic projection.
        color: str, optional
            Grid color.
        lw: float
            Grid line width.

        """
        self.ax.grid(color=color, lw=lw, **kwargs)

        if self.bg._proj == 'stereo':
            p = self.bg.paralleles(lats)
            m = self.bg.meridians(lons, nlats=nlats,
                                  lat_min=lat_min, lat_max=lat_max)

            self.plot(*p, color=color, lw=lw)
            self.plot(*m, color=color, lw=lw)

    def set_xlabel(self, *args, **kwargs):
        """Set x-label on map axis."""
        self.ax.set_xlabel(*args, **kwargs)

    def set_ylabel(self, *args, **kwargs):
        """Set y-label on map axis."""
        self.ax.set_ylabel(*args, **kwargs)

    def set_title(self, *args, **kwargs):
        """Set title on map axis."""
        self.ax.set_title(*args, **kwargs)

    def plot(self, lon_w, lat, *args, **kwargs):
        """Plot on the map."""
        return self.ax.plot(*self.bg(lon_w, lat), *args, **kwargs)

    def scatter(self, lon_w, lat, *args, **kwargs):
        """Scatter point(s) on the map."""
        return self.ax.scatter(*self.bg(lon_w, lat), *args, **kwargs)

    def text(self, lon_w, lat, txt, *args, **kwargs):
        """Text on the map."""
        self.ax.text(*self.bg(lon_w, lat), txt, *args, **kwargs)

    def add_path(self, path, **kwargs):
        """Add path on the map."""
        self.ax.add_patch(PathPatch(self.bg(path), **kwargs))

    def add_patch(self, patch, **kwargs):
        """Add patch on the map."""
        self.ax.add_patch(self.bg(patch), **kwargs)

    def add_collection(self, collection, **kwargs):
        """Add collection on the map."""
        self.ax.add_collection(self.bg(collection), **kwargs)


class MapAxes:
    """Multi axis map object.

    Parameters
    ----------
    bg: Map
        Background Map object.
    ax: matplotlib.axes._subplots.AxesSubplot or numpy.ndarray
        Matplotlib axis.
    bgshow: bool, optional
        Show basemap image (default: ``True``).
    ticks: bool, optional
        Show map X-Y ticks (default: ``True``).
    lim: bool, optional
        Set X-Y limits based on map extent (default: ``True``).
    grid: bool, optional
        Show default image grid (default: ``True``).

    """

    def __new__(cls, bg, ax, **kwargs):
        if np.ndim(ax) == 0:
            return MapAxis(bg, ax, **kwargs)

        if np.ndim(ax) == 1:
            return np.array([MapAxis(bg, axis, **kwargs) for axis in ax])

        if np.ndim(ax) == 2:
            return np.array([
                [MapAxis(bg, axis, **kwargs) for axis in _ax] for _ax in ax
            ])

        raise ValueError(f'Invalid axis dimension: {np.ndim(ax)}')
