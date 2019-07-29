"""Read VIMS data from ISIS file."""

import os
import re

import numpy as np

from .errors import VIMSError
from .isis import ISISCube


def get_img_id(fname):
    """Extract image ID from filename."""
    img_ids = re.findall(r'^(?:C)?\d{10}_\d+(?:_\d+)?', fname)

    if not img_ids:
        raise VIMSError(f'File `{fname}` name does not '
                        'match the correct ID pattern.')

    return img_ids[0]


class VIMS:
    """VIMS object from ISIS file.

    Parameters
    ----------
    fname: str
        Name of the VIMS cube file.
    root: str, optional
        Folder location of the data.
        Use ``$VIMS_DATA`` environment variable
        first or the local directory otherwise.
        You can manually force the local directory
        with ``root='.'``.

    """

    def __init__(self, fname, root=None):
        self.img_id = fname
        self.root = root
        self.fname = fname

    def __str__(self):
        return self.img_id

    def __repr__(self):
        return f'<{self.__class__.__name__}> Cube: {self}'

    def __matmul__(self, other):
        if isinstance(other, int):
            if not (1 <= other <= self.NB):
                raise VIMSError(f'Band `{other}` invalid. Must be between 1 and {self.NB}')

            return self.data[other-1, :, :]

        if isinstance(other, float):
            if not (self.wvlns[0] <= other <= self.wvlns[-1]):
                raise VIMSError(f'Wavelength `{other}` invalid. Must be '
                                f'between {self.wvlns[0]} and {self.wvlns[-1]}')

            # No interpolation. Take the closest wavelength.
            iwvln = np.argmin(np.abs(self.wvlns - other))
            return self.data[iwvln, :, :]

        if isinstance(other, tuple):
            if len(other) != 2:
                raise VIMSError(f'Tuple must have 2 values (Line, Sample).')

            L, S = other

            if not (1 <= L <= self.NL):
                raise VIMSError(f'Line `{L}` invalid. Must be between 1 and {self.NL}')

            if not (1 <= S <= self.NS):
                raise VIMSError(f'Sample `{S}` invalid. Must be between 1 and {self.NS}')

            return self.data[:, int(L) - 1, int(S) - 1]

        raise VIMSError('\n - '.join([
            f'Invalid format. Use:',
            'INT -> band',
            'FLOAT -> wavelength',
            '(INT, INT) -> Line, Sample',
        ]))

    @property
    def img_id(self):
        """Cube image ID."""
        return self.__img_id

    @img_id.setter
    def img_id(self, fname):
        self.__img_id = get_img_id(fname)

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
        """Data filename."""
        return self.__fname

    @fname.setter
    def fname(self, fname):
        self.__fname = fname
        self.__isis = None

    @property
    def filename(self):
        """Data absolute filename."""
        return os.path.join(self.root, self.fname)

    @property
    def isis(self):
        """ISIS cube."""
        if self.__isis is None:
            self.__isis = ISISCube(self.filename)
        return self.__isis

    @property
    def NB(self):
        """Number of bands."""
        return self.isis.NB

    @property
    def NL(self):
        """Number of lines."""
        return self.isis.NL

    @property
    def NS(self):
        """Number of samples."""
        return self.isis.NS

    @property
    def shape(self):
        """Data shape."""
        return self.isis.shape

    @property
    def data(self):
        """Data cube."""
        return self.isis.cube

    @property
    def bands(self):
        """Cube bands numbers."""
        return self.isis.bands

    @property
    def b(self):
        """Cube bands numbers shortcut."""
        return self.bands

    @property
    def wvlns(self):
        """Cube central wavelengths (um)."""
        return self.isis.wvlns

    @property
    def w(self):
        """Cube central wavelengths (um) shortcut."""
        return self.wvlns

    @property
    def extent(self):
        """Cube images extent."""
        return [.5, self.NS + .5, self.NL + .5, .5]

    @property
    def sticks(self):
        """Cube sample ticks."""
        return [1, self.NS // 4, self.NS // 2, self.NS // 4 + self.NS // 2, self.NS]

    @property
    def lticks(self):
        """Cube line ticks."""
        return [1, self.NL // 4, self.NL // 2, self.NL // 4 + self.NL // 2, self.NL]

    @property
    def bticks(self):
        """Cube bands ticks."""
        return [1, self.NB // 4, self.NB // 2, self.NB // 4 + self.NB // 2, self.NB]

    @property
    def wticks(self):
        """Cube wvlns ticks."""
        w = self.wvlns
        wi = [w[k * self.NB // 6 - 1] for k in range(1, 6)]
        return [w[0], *wi, w[-1]]

    @property
    def slabel(self):
        """Cube sample label."""
        return 'Samples'

    @property
    def llabel(self):
        """Cube line label."""
        return 'Lines'

    @property
    def blabel(self):
        """Cube band label."""
        return 'Bands'

    @property
    def wlabel(self):
        """Cube wavelength label."""
        return 'Wavelength (um)'

    @property
    def ilabel(self):
        """Cube I/F label."""
        return 'I/F'

    @property
    def start(self):
        """Cube start time (UTC)."""
        return self.isis.start

    @property
    def stop(self):
        """Cube stop time (UTC)."""
        return self.isis.stop

    @property
    def duration(self):
        """Cube acquisition duration."""
        return self.isis.duration

    @property
    def time(self):
        """Cube mid time (UTC)."""
        return self.isis.time
