"""VIMS RAW QUB data module."""

import os
from datetime import datetime as dt

import numpy as np

import pvl

from .cassini import img_id


def _dt(time):
    """Parse time as datetime."""
    return dt.strptime(time[:-1], '%Y-%jT%H:%M:%S.%f')


class QUB:
    """VIMS RAW QUB object.

    Parameters
    ----------
    filename: str
        Input filename.
    root: str, optional
        Folder location of the data.
        Use ``$VIMS_DATA`` environment variable
        first or the local directory otherwise.
        You can manually force the local directory
        with ``root='.'``.

    Raises
    ------
    FileNotFoundError
        If the file does not exists locally.
    IOError
        If the file is not a valid QUB file.

    """

    def __init__(self, fname, root=None):
        self.img_id = img_id(fname)
        self.root = root

        if not self.is_file:
            raise FileNotFoundError(f'File `{self.filename}` not found.')

        if not self.is_qub:
            raise IOError(f'File `{self.filename}` is not a valid QUB.')

        self.__header = None
        self.__cube = None
        self.__back_plane = None
        self.__side_plane = None

    def __str__(self):
        return self.img_id

    def __repr__(self):
        return ('\n - '.join([
            f'<{self.__class__.__name__}> QUB: {self}',
            f'Size: {self.ns, self.nl}',
            f'Mode: {self.sampling_mode_vis, self.sampling_mode_ir}',
            f'Start time: {self.start}',
            f'Stop time: {self.stop}',
            f'Exposure: {self.expo_vis, self.expo_ir} sec',
            f'Duration: {self.duration}',
            f'Target: {self.target}',
        ]))

    def __getitem__(self, val):
        if isinstance(val, tuple) and len(val) == 2:
            return self.get_img(*val)

        if isinstance(val, (int, slice)):
            return self.get_spectrum(val)

        if isinstance(val, str):
            return self.core[val]

        raise ValueError('\n - '.join([
            f'Invalid format (1-index). Use:',
            'INT -> Band image',
            '[INT, INT] -> [Sample, Line] spectrum',
        ]))

    @property
    def root(self):
        """Data root folder."""
        return self.__root

    @root.setter
    def root(self, root):
        if root is None:
            if 'VIMS_DATA' in os.environ:
                root = os.environ['VIMS_DATA']
            else:
                root = os.getcwd()

        elif not os.path.isdir(root):
            raise OSError(f'Folder `{root}` does not exists.')

        self.__root = root

    @property
    def fname(self):
        """QUB filename."""
        return f'v{self}.qub'

    @property
    def filename(self):
        """Data absolute filename."""
        return os.path.join(self.root, self.fname)

    @property
    def is_file(self):
        """Check if file exists."""
        return os.path.exists(self.filename)

    @property
    def is_qub(self):
        """Check if the file is a valid QUB."""
        with open(self.filename, 'r') as f:
            head = f.read(512)

        return '^QUBE' in head

    @property
    def header(self):
        """Extract QUB header content in PVL format."""
        if self.__header is None:
            self.__header = pvl.load(self.filename)
        return self.__header

    @property
    def b_record(self):
        """Records size (bytes)."""
        return int(self.header['RECORD_BYTES'])

    @property
    def b_header(self):
        """Header size (bytes)."""
        return int(self.header['^QUBE'] - 1) * self.b_record

    @property
    def core(self):
        """QUB header core metadata."""
        return self.header['QUBE']

    @property
    def instrument_id(self):
        """Instrument ID."""
        return self.core['INSTRUMENT_ID']

    @property
    def axis_name(self):
        """Data axis name order."""
        return self.core['AXIS_NAME']

    @property
    def index_sample(self):
        """Data sample axis index."""
        return self.axis_name.index('SAMPLE')

    @property
    def index_line(self):
        """Data line axis index."""
        return self.axis_name.index('LINE')

    @property
    def index_band(self):
        """Data band axis index."""
        return self.axis_name.index('BAND')

    @property
    def core_items(self):
        """Core items sizes."""
        return self.core['CORE_ITEMS']

    @property
    def suffix_items(self):
        """Suffix items sizes."""
        return self.core['SUFFIX_ITEMS']

    @property
    def ns(self):
        """Number of samples."""
        return int(self.core_items[self.index_sample])

    @property
    def nl(self):
        """Number of lines."""
        return int(self.core_items[self.index_line])

    @property
    def nb(self):
        """Number of bands."""
        return int(self.core_items[self.index_band])

    @property
    def ss(self):
        """Number of samples suffix."""
        return int(self.suffix_items[self.index_sample])

    @property
    def sl(self):
        """Number of lines suffix."""
        return int(self.suffix_items[self.index_line])

    @property
    def sb(self):
        """Number of bands suffix."""
        return int(self.suffix_items[self.index_band])

    def name(self, tag):
        """Tag name."""
        return self.core[tag + '_NAME']

    def unit(self, tag):
        """Tag unit."""
        return self.core[tag + '_UNIT']

    def item_bytes(self, tag):
        """Tag item bytes."""
        return self.core[tag + '_ITEM_BYTES']

    def item_type(self, tag):
        """Tag item type."""
        return self.core[tag + '_ITEM_TYPE']

    def bin_type(self, tag):
        """Tag byte format."""
        _type = self.item_type(tag)
        _bytes = self.item_bytes(tag)

        is_list = isinstance(_type, list)
        if not is_list:
            _type = [_type]
            _bytes = [_bytes]

        out = []
        for t, b in zip(_type, _bytes):
            arch = '>' if t == 'SUN_INTEGER' else '<'  # Big | Little endian

            if b == 2:
                byte = 'i2'
            elif b == 4:
                byte = 'i4'
            else:
                raise ValueError('Invalid `ITEM_BYTES`')

            out.append(arch + byte)

        return np.dtype(', '.join(out))

    def base(self, tag):
        """Tag base."""
        return self.core[tag + '_BASE']

    def multiplier(self, tag):
        """Tag multiplier."""
        return self.core[tag + '_MULTIPLIER']

    def null(self, tag):
        """Tag null."""
        return self.core[tag + '_NULL']

    @property
    def b_band_suffix(self):
        """Band suffix size (bytes)."""
        return np.sum(self.item_bytes('BAND_SUFFIX'))

    @property
    def b_bands_suffix(self):
        """Bands suffix size (bytes)."""
        return (self.ns + self.ss) * self.b_band_suffix

    @property
    def b_sample_suffix(self):
        """Sample suffix size (bytes)."""
        return self.item_bytes('SAMPLE_SUFFIX')

    @property
    def b_samples_suffix(self):
        """Samples suffix size (bytes)."""
        return self.ss * self.b_sample_suffix

    @property
    def b_sample(self):
        """Sample size (bytes)."""
        return self.item_bytes('CORE')

    @property
    def b_samples(self):
        """Sample size (bytes)."""
        return self.ns * self.b_sample

    @property
    def b_band(self):
        """Band size (bytes)."""
        return self.b_samples + self.b_samples_suffix

    @property
    def b_bands(self):
        """Bands size (bytes)."""
        return self.nb * self.b_band

    @property
    def b_line(self):
        """Line size (bytes)."""
        return self.b_bands + self.b_bands_suffix

    @property
    def b_lines(self):
        """Lines size (bytes)."""
        return self.nl * self.b_line

    @property
    def b_cube(self):
        """Cube size (bytes)."""
        return np.product(self.shape_cube) * self.b_sample

    @property
    def shape_cube(self):
        """Cube shape."""
        return (self.nl, self.nb, self.ns)

    @property
    def dtype_cube(self):
        """Data type cube."""
        return self.bin_type('CORE')

    @property
    def b_back_plane(self):
        """Back plane size (bytes)."""
        return np.product(self.shape_back_plane) * self.b_band_suffix

    @property
    def shape_back_plane(self):
        """Back plane shape."""
        return (self.nl, self.ns + self.ss)

    @property
    def dtype_back_plane(self):
        """Data type back plane."""
        return self.bin_type('BAND_SUFFIX')

    @property
    def b_side_plane(self):
        """Side plane size (bytes)."""
        return np.product(self.shape_side_plane) * self.b_samples_suffix

    @property
    def shape_side_plane(self):
        """Side plane shape."""
        return (self.nl, self.nb)

    @property
    def dtype_side_plane(self):
        """Data type Side plane."""
        return self.bin_type('SAMPLE_SUFFIX')

    @property
    def b_extra(self):
        """Extra bytes af the end to complete the record."""
        return (self.b_lines % self.b_record) * b' '

    def _load_data(self):
        """Load cube data."""
        if self.axis_name != ['SAMPLE', 'BAND', 'LINE']:
            raise ValueError(f'Invalid `AXIS_NAME`: `{self.axis_name}`.')

        # Load binary data
        with open(self.filename, 'rb') as f:
            # Skip Ascii header
            f.seek(self.b_header, os.SEEK_SET)

            # Load binary block
            raw = f.read(self.b_lines)

        # Extract data
        raw = np.frombuffer(raw, dtype='b')
        raw = raw.reshape(self.nl, self.b_line)

        lines = raw[:, :self.b_bands]
        raw_back_plane = raw[:, self.b_bands:]

        bands = lines.reshape(self.nl, self.nb, self.b_band)

        cube = bands[:, :, :self.b_samples]
        raw_side_plane = bands[:, :, self.b_samples:]

        cube = cube.reshape(self.b_cube)
        cube = np.frombuffer(cube, dtype=self.dtype_cube)
        cube = cube.reshape(self.shape_cube)

        back_plane = raw_back_plane.reshape(self.b_back_plane)
        back_plane = np.frombuffer(back_plane, dtype=self.dtype_back_plane)
        back_plane = back_plane.reshape(self.shape_back_plane)

        side_plane = raw_side_plane.reshape(self.b_side_plane)
        side_plane = np.frombuffer(side_plane, dtype=self.dtype_side_plane)
        side_plane = side_plane.reshape(self.shape_side_plane)

        # Cache cube data and clear arrays
        del raw, lines, bands, raw_back_plane, raw_side_plane
        self.__cube = np.ma.array(cube, mask=(cube < 0), fill_value=0)
        self.__back_plane = back_plane
        self.__side_plane = side_plane

    @property
    def data(self):
        """Cube data (NS, NB, NL)."""
        if self.__cube is None:
            self._load_data()
        return self.__cube

    @property
    def back_plane(self):
        """Cube back plane (NL, NS + SS)."""
        if self.__back_plane is None:
            self._load_data()
        return self.__back_plane

    @property
    def side_plane(self):
        """Cube side plane (NL, NB)."""
        if self.__side_plane is None:
            self._load_data()
        return self.__side_plane

    @property
    def extent(self):
        """Pyplot imshow cube extent."""
        return [.5, self.ns + .5, self.nl + .5, .5]

    @property
    def cextent(self):
        """Pyplot contour cube extent."""
        return [.5, self.ns + .5, .5, self.nl + .5]

    @property
    def sticks(self):
        """Cube sample ticks."""
        return [1, self.ns // 4, self.ns // 2, self.ns // 4 + self.ns // 2, self.ns]

    @property
    def lticks(self):
        """Cube line ticks."""
        return [1, self.nl // 4, self.nl // 2, self.nl // 4 + self.nl // 2, self.nl]

    @staticmethod
    def check_index(value, n, name):
        """Check index array value range."""
        if value is None:
            return None
        if value < 1:
            raise ValueError(f'{name.title()} number `{value}` should be ≥ 1.')
        if value > n:
            raise ValueError(f'{name.title()} number `{value}` should be ≤ {n}.')
        return int(value) - 1

    def check_type(self, value, n, name):
        """Check index array value type.

        Note
        ----
        If a slice is provided, start and stop values will be included.

        """
        if value is None:
            return None

        if isinstance(value, int):
            return self.check_index(value, n, name)

        if isinstance(value, slice):
            start = self.check_index(value.start, n, name)
            stop = None if value.stop is None \
                else self.check_index(value.stop, n, name) + 1
            return slice(start, stop, value.step)

        raise ValueError(f'Invalid {name} type: `{type(value)}`.')

    def isample(self, sample):
        """Get sample index."""
        return self.check_type(sample, self.ns, 'Sample')

    def iline(self, line):
        """Get line index."""
        return self.check_type(line, self.nl, 'Line')

    def iband(self, band):
        """Get band index."""
        return self.check_type(band, self.nb, 'Band')

    def get_img(self, sample, line):
        """Extract sample and line image."""
        return self.data[self.isample(sample), :, self.iline(line)]

    def get_spectrum(self, band):
        """Extract band spectrum."""
        return self.data[:, self.iband(band), :]

    @property
    def expo(self):
        """Cube exposure duration (IR, VIS) in secondes."""
        return tuple(np.multiply(self.core['EXPOSURE_DURATION'], 1e-3))

    @property
    def expo_vis(self):
        """Cube VIS exposure duration (sec)."""
        return self.expo[1]

    @property
    def expo_ir(self):
        """Cube IR exposure duration (sec)."""
        return self.expo[0]

    @property
    def sampling_mode_id(self):
        """Cube sampling mode (IR, VIS spatial, VIS spectral)."""
        return tuple(self.core['SAMPLING_MODE_ID'])

    @property
    def sampling_mode_ir(self):
        """Cube IR sampling mode."""
        return self.sampling_mode_id[0]

    @property
    def sampling_mode_vis(self):
        """Cube VIS spatial and spatial sampling modes."""
        return self.sampling_mode_id[1:]

    @property
    def target(self):
        """Target name."""
        return self.core['TARGET_NAME']

    @property
    def start(self):
        """Acquisition start time (UTC)."""
        return _dt(self.core['START_TIME'])

    @property
    def stop(self):
        """Acquisition stop time (UTC)."""
        return _dt(self.core['STOP_TIME'])

    @property
    def duration(self):
        """Acquisition dureation."""
        return self.stop - self.start
