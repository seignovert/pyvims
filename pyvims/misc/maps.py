"""Background maps module."""

import os
import re

import numpy as np

from matplotlib.image import imread
from matplotlib.path import Path
from matplotlib.patches import PathPatch

from ..projections.stereographic import r_stereo, xy as xy_stereo
from ..vars import ROOT_DATA
from ..vectors import deg180, deg360


ROOT = root = os.path.join(ROOT_DATA, 'maps')


def parse(rexp, line):
    """Parse README line.

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
        filename = os.path.join(ROOT, 'README.md')

        if not os.path.exists(filename):
            with open(filename, 'w') as f:
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

        return filename

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

        print(f'Image `{key}` saved in map registry.')

    @classmethod
    def remove(cls, fname):
        """Remove a map file from README."""
        key = basename(fname)

        if key in cls.maps().keys():
            remove_from_readme(cls.filename(), key)
            del cls.__maps[key]

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

    """

    def __init__(self, fname, root=None, extent=None, src=None, url=None,
                 projection=None, name=None):
        self.root = root if root else ROOT
        self.fname = fname

        self.data_extent = list(extent)
        self.src = src
        self.url = url
        self.proj = projection.lower() if isinstance(projection, str) else None

        self.name = name if name is not None else \
            '.'.join(self.fname.split('.')[:-1])

    def __str__(self):
        return self.fname if self.root == ROOT else self.filename

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
        if len(args) == 1 and isinstance(args[0], PathPatch):
            return self.xy_patch(args[0])

        if len(args) == 2:
            return self.xy(args[0], args[1])

        raise ValueError('A `PathPatch` or 2 attributes are required (lon_w, lat)')

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
        """Convert point coordinate on the map coordinates.

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
            if self.data_extent[0] < self.data_extent[1]:
                return deg180(-lon_w), lat  # East longitude ]-180°, 180°]
            return deg360(lon_w), lat

        if self._proj == 'stereo':
            return xy_stereo(lon_w, lat, n_pole=self.n_pole)

        return self.data_extent

    def xy_patch(self, patch):
        """Convert patch vertices on the map coordinates.

        Parameters
        ----------
        patch: matplotlib.patches.PathPatch
            Pyplot patch.

        Returns
        -------
        matplotlib.patches.PathPatch
            Re-projected patch in map coordinates.

        """
        path = patch.get_path()
        vertices = np.transpose(self.xy(*path.vertices.T))

        return PathPatch(
            Path(vertices, path.codes),
            edgecolor=patch.get_ec(),
            facecolor=patch.get_fc(),
        )

    def lons(self, lon_min=None, lon_max=None, npts=None):
        """Get longitude grid.

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
        lons = np.linspace(
            min(self.data_extent[:2]) if lon_min is None else lon_min,
            max(self.data_extent[:2]) if lon_max is None else lon_max,
            13 if npts is None else npts,
        )

        if self.data_extent[0] > self.data_extent[1]:
            lons = lons[::-1]  # Revert x-axis

        return lons

    def lats(self, lat_min=None, lat_max=None, npts=None):
        """Get latitude grid.

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
        return np.linspace(
            min(self.data_extent[2:]) if lat_min is None else lat_min,
            max(self.data_extent[2:]) if lat_max is None else lat_max,
            7 if npts is None else npts,
        )

    @property
    def xlim(self):
        """X-axis limits based on image background."""
        return self.extent[0], self.extent[1]

    @property
    def ylim(self):
        """Y-axis limits based on image background."""
        return self.extent[2], self.extent[3]
