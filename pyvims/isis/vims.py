"""Read VIMS data from ISIS file."""

import os
import re

import numpy as np

from .camera import VIMSCamera
from .errors import VIMSError
from .isis import ISISCube
from .quaternions import m2q, q_mult, q_rot
from .time import hex2double
from .vectors import hat, radec, v_max_dist


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

    # VIMS clock drift for IR scan
    VIMS_SEC = 1.01725

    def __init__(self, fname, root=None):
        self.img_id = fname
        self.root = root
        self.fname = fname

    def __str__(self):
        return self.img_id

    def __repr__(self):
        return f'<{self.__class__.__name__}> Cube: {self} [{self.channel}]'

    def __matmul__(self, other):
        if isinstance(other, int):
            if not (self.bands[0] <= other <= self.bands[-1]):
                raise VIMSError(f'Band `{other}` invalid. Must be '
                                f'between {self.bands[0]} and {self.bands[-1]}')

            # No interpolation. Take the closest wavelength.
            iband = np.argmin(np.abs(self.bands - other))
            return self.data[iband, :, :]

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
        self.__et = None
        self.__camera = None
        self.__pixels = None
        self.__sky = None

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
    def NP(self):
        """Number of pixels."""
        return self.NL * self.NS

    @property
    def shape(self):
        """Data shape."""
        return self.isis.shape

    def _flat(self, array):
        """Flatten grid array.

        Parameters
        ----------
        array: list or np.array
            Grid array to flatten.

        Returns
        -------
        np.array
            Flattenned array.

        """
        ndim = int(np.product(np.shape(array)) / self.NP)
        return np.reshape(array, (ndim, self.NP))

    def _grid(self, array):
        """Grid flatten array.

        Parameters
        ----------
        array: list or np.array
            Flatten array.

        Returns
        -------
        np.array
            Gridded array.

        """
        ndim = int(np.product(np.shape(array)) / self.NP)
        return np.reshape(array, (ndim, self.NL, self.NS))

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

    @property
    def native_start(self):
        """Native start time."""
        return self.isis._inst['NativeStartTime']

    @property
    def native_stop(self):
        """Native stop time."""
        return self.isis._inst['NativeStopTime']

    def _clock_et(self, time):
        """Convert clock ET from hex format to double."""
        clock, ticks = str(time).split('.', 1)
        et = hex2double(self.isis._naif[f'CLOCK_ET_-82_{clock}_COMPUTED'])
        return et + int(ticks) / 15959

    @property
    def et_start(self):
        """Computed ET at native start time."""
        return self._clock_et(self.native_start)

    @property
    def et_stop(self):
        """Computed ET at native stop time."""
        return self._clock_et(self.native_stop)

    @property
    def channel(self):
        """Cube channel."""
        return self.isis._inst['Channel']

    @property
    def _expo_ir(self):
        """IR exposure duration in secondes.

        Corrected for the VIMS-IR clock drift (``x 1.01725``).

        See also
        --------
        PDS: `VIMS-IR pixel timing`_ report.

        .. _`VIMS-IR pixel timing`: https://pds-atmospheres.nmsu.edu/data_and_services/
            atmospheres_data/Cassini/logs/VIMS%20IR%20Pixel%20Timing_final.pdf

        """
        for v, u in self.isis.exposure:
            if u == 'IR':
                return v * self.VIMS_SEC / 1e3
        return None

    @property
    def _is_ir(self):
        """Boolean test if the cube channel is ``IR``."""
        return self.channel == 'IR'

    @property
    def _expo_vis(self):
        """Visible exposure duration in secondes.

        Not corrected for the VIMS-IR timing factor.

        See also
        --------
        ISIS3: `VIMS-VIS Camera`_ implementation.

        .. _`VIMS-VIS Camera`: https://github.com/USGS-Astrogeology/ISIS3/blob/
            af857368a3adadd6870ee551c91cbfd4ea60ac1b/isis/src/cassini/objs/
            VimsCamera/VimsSkyMap.cpp#L87

        """
        for v, u in self.isis.exposure:
            if u == 'VIS':
                return v / 1e3
        return None

    @property
    def expo(self):
        """Cube exposure based on `channel`."""
        return self._expo_ir if self._is_ir else self._expo_vis

    @property
    def interline_delay(self):
        """VIMS interline delay in seconds."""
        return self.isis._inst['InterlineDelayDuration'] * self.VIMS_SEC / 1e3

    @property
    def _s(self):
        """Camera samples array."""
        return np.array([np.arange(1, self.NS + 1)])

    @property
    def _l(self):
        """Camera lines array."""
        return np.transpose([np.arange(1, self.NL + 1)])

    @property
    def _et_ir(self):
        """IR pixels ephemeris time (ET)."""
        line_duration = self.NS * self._expo_ir + self.interline_delay
        return (self.et_start
                + (self._l - 1) * line_duration
                + (self._s - .5) * self._expo_ir)

    @property
    def _et_vis(self):
        """Visible pixels ephemeris time (ET).

        VIS exposure is for a single line. According to SIS,
        ``NATIVE_START_TIME`` is for the first pixel of the IR exposure.

        The offset from IR start to VIS start is calculated by:

            (IrExposMsec - VisExposMsec) / 2

        """
        offset = .5 * (self.NS * self._expo_ir - self._expo_vis)
        return (self.et_start + offset
                + (self._l - .5) * self._expo_vis
                + 0 * self._s)

    @property
    def et(self):
        """Pixels ephemeris time based on channel."""
        if self.__et is None:
            self.__et = self._et_ir if self._is_ir else self._et_vis
        return self.__et

    @property
    def mode(self):
        """Cube sampling mode."""
        return self.isis._inst['SamplingMode']

    @property
    def camera(self):
        """VIMS camera."""
        if self.__camera is None:
            offsets = [self.isis._inst['XOffset'], self.isis._inst['ZOffset']]
            swaths = [self.isis._inst['SwathWidth'], self.isis._inst['SwathLength']]
            self.__camera = VIMSCamera(self.channel, self.mode, offsets, swaths)
            self.__pixels = None
            self.__sky = None
        return self.__camera

    @property
    def _cassini_pointing(self):
        """Cassini pointing attitude.

        The spacecraft pointing is extracted from
        ISIS tables and linearly interpolated on pixel
        ephemeris times. All quaternions are renormalized
        to 1. And additional rotation (labeled
        ``ConstantRotation`` in the header) is required to
        get the actual instrument pointing (see
        :py:func:`_inst_rot`).

        Note
        ----
        Quaternions should be interpolated together with
        Slerp method (see :py:func:`angles.q_interp`).
        But most of the time the drift of the pointing
        between the recorded ETs values is small enough
        to use a linerar interpolation.

        Returns
        -------
        np.array
            Grid (Nl, NS) of SPICE quaternions of the spacecraft
            pointing attitude.

        """
        p = self.isis.tables['InstrumentPointing'].data
        q0 = p['J2000Q0']
        q1 = p['J2000Q1']
        q2 = p['J2000Q2']
        q3 = p['J2000Q3']
        ets = p['ET']

        p = self._flat([
            np.interp(self.et, ets, q0),
            np.interp(self.et, ets, q1),
            np.interp(self.et, ets, q2),
            np.interp(self.et, ets, q3),
        ])

        return self._grid(hat(p))

    @property
    def _inst_rot(self):
        """Instrument rotation matrix from the spacecraft frame."""
        return np.reshape(
            self.isis.tables['InstrumentPointing']['ConstantRotation'], (3, 3))

    @property
    def _inst_q(self):
        """Instrument boresight pointing."""
        q = q_mult(m2q(self._inst_rot), self._flat(self._cassini_pointing))
        return self._grid(q)

    @property
    def pixels(self):
        """Camera pixel pointing direction in J2000 frame."""
        if self.__pixels is None:
            self.__pixels = q_rot(self._inst_q, self.camera.pixels)
            self.__sky = None
        return self.__pixels

    @property
    def sky(self):
        """Camera pixel pointing direction in J2000 frame."""
        if self.__sky is None:
            self.__sky = radec(self.pixels)
        return self.__sky

    @property
    def pointing(self):
        """Mean camera pointing.

        Returns
        -------
        float, float, float
            Mean right-ascension, mean declination and fov radius (in degrees).

        """
        ra, dec = radec(np.mean(self.pixels, axis=(1, 2)))

        # Search FOV max diameter
        vecs = self._flat(self.pixels)
        imaxs = v_max_dist(vecs)
        fov = np.degrees(np.arccos(np.dot(vecs[:, imaxs[0]], vecs[:, imaxs[1]])))

        return ra, dec, fov / 2
