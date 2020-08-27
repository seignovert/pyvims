"""Read VIMS data from ISIS file."""

import os
import re

import numpy as np

from requests import HTTPError

from .camera import VIMSCamera
from .cassini import img_id
from .contour import VIMSContour
from .constantes import AU
from .errors import VIMSError
from .flyby import FLYBYS
from .img import rgb, save_img
from .isis import ISISCube, hex2double
from .misc import great_circle_patch
from .pixel import VIMSPixels
from .plot import plot_cube
from .projections import ortho_proj
from .quaternions import m2q, q_mult, q_rot, q_rot_t
from .star import Star
from .target import intersect
from .vars import VIMS_DATA_PORTAL
from .vectors import (angle, azimuth, deg180, hat, hav_dist,
                      lonlat, norm, radec, v_max_dist)
from .wget import wget
from .wvlns import ir_hot_pixels


def _parse(val):
    """Parse index values based on type or format."""
    if isinstance(val, (int, float, slice, np.int64)):
        return val

    if isinstance(val, (tuple, list)):
        values = ()
        for v in val:
            values += (_parse(v),)
        return values

    if isinstance(val, str):
        if val.lower() == 'surface':
            return _parse(('165:169', '138:141', '212:213'))

        if val.lower() == 'surface 2':
            return _parse(('339:351', '138:141', '121:122'))

        if val.lower() == 'surface 3':
            return _parse(('339:351', '207:213', '165:169'))

        if val.lower() == '5um':
            return _parse('339:351')

        s = re.findall(r'^\d+$', val)
        if s:
            return int(s[0])

        s = re.findall(r'^\d+\.\d*$', val)
        if s:
            return float(s[0])

        s = re.findall(r'^\d+:\d+$', val)
        if s:
            s = re.findall(r'\d+', val)
            return slice(int(s[0]), int(s[1]))

        s = re.findall(r'^\d+\.\d*:\d+\.\d*$', val)
        if s:
            s = re.findall(r'\d+\.\d*', val)
            return slice(float(s[0]), float(s[1]))

    raise TypeError(f'Value: `{val}` has invalid a unknown type: `{type(val)}`.')


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
    download: bool, optional
        Enable download cube data from the VIMS data portal
        if not locally present on the disk.

    """

    # VIMS clock drift for IR scan
    VIMS_SEC = 1.01725

    def __init__(self, fname, root=None, download=True,
                 channel='ir', prefix='C', suffix='', ext='cub'):
        self.img_id = img_id(fname)
        self.fname = f'{prefix}{self.img_id}{suffix}_{channel}.{ext}'
        self.root = root
        self.download = download

    def __str__(self):
        return self.img_id

    def __repr__(self):
        return ('\n - '.join([
            f'<{self.__class__.__name__}> Cube: {self}',
            f'Size: {self.NS, self.NL}',
            f'Channel: {self.channel}',
            f'Mode: {self.mode}',
            f'Start time: {self.start}',
            f'Stop time: {self.stop}',
            f'Exposure: {self.expo} sec',
            f'Duration: {self.duration}',
            f'Main target: {self.target_name}',
            f'Flyby: {self.flyby}',
        ]))

    def __getitem__(self, val):
        val = _parse(val)

        if isinstance(val, (int, float, slice)):
            return self._img(val)

        if isinstance(val, tuple):
            if len(val) == 2:
                if isinstance(val[0], float) and isinstance(val[1], float):
                    return self.get_pixel(*val)
                return self.pixels[val]

            if len(val) == 3:
                return self._rgb(*val)

        raise VIMSError('\n - '.join([
            'Invalid format. Use:',
            'INT -> Band image',
            'FLOAT -> Wavelength image',
            '[INT, INT] -> Sample, Line pixel',
            '[FLOAT, FLOAT] -> West Longitude, Latitude pixel',
            '[INT, INT, INT] -> Bands RGB',
            '[FLOAT, FLOAT, FLOAT] -> Wavelengths RGB',
        ]))

    def __matmul__(self, val):
        return self[val]

    def __call__(self, *args, **kwargs):
        """Call plot function by default."""
        if not args:
            args = ['surface' if self._is_ir else 75]
        return self.plot(*args, **kwargs)

    def __eq__(self, other):
        """Compare two cubes."""
        if isinstance(other, str):
            return str(self) == other
        if hasattr(other, 'md5'):
            return self.md5 == other.md5
        return False

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

        self.__root = str(root)

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
        self.__j2000 = None
        self.__sky = None
        self.__xyz = None
        self.__lonlat = None
        self.__alt = None
        self.__ill = None
        self.__cxyz = None
        self.__contour = None
        self.__rsky = None
        self.__rxyz = None
        self.__rlonlat = None
        self.__rlimb = None
        self.__rpath_180 = None
        self.__rpath_360 = None
        self.__fsky = None
        self.__fxyz = None
        self.__flonlat = None
        self.__flimb = None
        self.__fpath_180 = None
        self.__fpath_360 = None
        self.__spec_pix = None
        self.__spec_pts = None
        self.__spec_mid_pt = None
        self.__pixels = None

    @property
    def filename(self):
        """Data absolute filename."""
        return os.path.join(self.root, self.fname)

    @property
    def url(self):
        """Data URL on the VIMS Data Portal."""
        return f'{VIMS_DATA_PORTAL}/cube/{self.fname}'

    def download_cube(self, overwrite=False):
        """Download cube from the VIMS Data Portal.

        Parameters
        ----------
        overwrite: bool, optional
            Enable file overwrite.

        """
        try:
            wget(self.url, filename=self.filename, overwrite=overwrite)
        except HTTPError:
            raise FileNotFoundError(f'`{self.fname}` is not available on '
                                    'the VIMS Data Portal.')

    @property
    def isis(self):
        """ISIS cube."""
        if self.__isis is None:
            try:
                self.__isis = ISISCube(self.filename)
            except FileNotFoundError as err:
                if self.download:
                    self.download_cube()
                    self.__isis = ISISCube(self.filename)
                else:
                    raise err

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

    @property
    def md5(self):
        """Cube MD5 hash."""
        return self.isis.md5

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

    @staticmethod
    def _mean(arr):
        """Mean cube values."""
        return np.mean(arr, axis=(1, 2))

    @staticmethod
    def _med(arr):
        """Median cube values."""
        return np.median(arr, axis=(1, 2))

    @staticmethod
    def _std(arr):
        """Standard deviation cube values."""
        return np.std(arr, axis=(1, 2))

    @staticmethod
    def _min(arr):
        """Minimum cube values."""
        return np.min(arr, axis=(1, 2))

    @staticmethod
    def _max(arr):
        """Maximum cube values."""
        return np.max(arr, axis=(1, 2))

    @property
    def history(self):
        """Cube history."""
        return self.isis.history

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
        """Cube central wavelengths (µm)."""
        return self.isis.wvlns

    @property
    def w(self):
        """Cube central wavelengths (µm) shortcut."""
        return self.wvlns

    @property
    def wavenumbers(self):
        """Cube central wavenumber (cm^-1)."""
        return 1e4 / self.wvlns

    @property
    def sigma(self):
        """Cube central wavenumber (cm^-1) shortcut."""
        return self.wavenumbers

    @property
    def extent(self):
        """Pyplot imshow cube extent."""
        return [.5, self.NS + .5, self.NL + .5, .5]

    @property
    def cextent(self):
        """Pyplot contour cube extent."""
        return [.5, self.NS + .5, .5, self.NL + .5]

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
        return [97, 150, 200, 250, 300, 352] if self._is_ir else \
            [1, 25, 50, 75, 96]

    @property
    def wticks(self):
        """Cube wvlns ticks."""
        return np.arange(1, 5.5, .5) if self._is_ir else \
            np.arange(.4, 1.2, .2)

    @property
    def nticks(self):
        """Cube wavenumbers ticks."""
        return np.arange(2000, 12000, 500) if self._is_ir else []

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
        return 'Wavelength (µm)'

    @property
    def nlabel(self):
        """Cube wavenumber label."""
        return r'Wavenumber (cm$^{-1}$)'

    @property
    def ilabel(self):
        """Cube I/F label."""
        return 'I/F'

    @property
    def obs_id(self):
        """Cube observation ID from Archive."""
        return self.isis.header['Archive']['ObservationId']

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
    def mode(self):
        """Cube sampling mode."""
        return self.isis._inst['SamplingMode']

    @property
    def _is_hr(self):
        """Boolean test if the cube sampling is ``HI-RES``."""
        return self.mode == 'HI-RES'

    @property
    def _is_ir_hr(self):
        """Boolean test if the cube channel is ``IR`` and sampling is ``HI-RES``."""
        return self._is_ir and self._is_hr

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
        """Image samples array."""
        return np.array([np.arange(1, self.NS + 1)])

    @property
    def _l(self):
        """Image lines array."""
        return np.transpose([np.arange(1, self.NL + 1)])

    @property
    def _sl(self):
        """Image samples and lines grid."""
        return np.array(np.meshgrid(self._s, self._l))

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
    def et_median(self):
        """Median ephemeris time."""
        return self._med([self.et])[0]

    @property
    def target_name(self):
        """Main target name from ISIS header."""
        return self.isis.target_name

    @property
    def target_radius(self):
        """Main target radius from ISIS header."""
        return self.isis.target_radius

    @property
    def camera(self):
        """VIMS camera."""
        if self.__camera is None:
            offsets = [self.isis._inst['XOffset'], self.isis._inst['ZOffset']]
            swaths = [self.isis._inst['SwathWidth'], self.isis._inst['SwathLength']]
            self.__camera = VIMSCamera(self.channel, self.mode, offsets, swaths)
            self.__j2000 = None
            self.__sky = None
            self.__xyz = None
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
            self.__cxyz = None
            self.__contour = None
            self.__rsky = None
            self.__rxyz = None
            self.__rlonlat = None
            self.__rlimb = None
            self.__fsky = None
            self.__fxyz = None
            self.__flonlat = None
            self.__flimb = None
            self.__spec_pix = None
            self.__spec_pts = None
            self.__spec_mid_pt = None
            self.__pixels = None
        return self.__camera

    def _cassini_pointing(self, et):
        """Cassini pointing attitude.

        The spacecraft pointing is extracted from
        ISIS tables and linearly interpolated on pixel
        ephemeris times. All quaternions are renormalized
        to 1. And additional rotation (labeled
        ``ConstantRotation`` in the header) is required to
        get the actual instrument pointing (see
        :py:func:`_q_inst`).

        Note
        ----
        Quaternions should be interpolated together with
        Slerp method (see :py:func:`angles.q_interp`).
        But most of the time the drift of the pointing
        between the recorded ETs values is small enough
        to use a linear interpolation.

        Parameters
        ----------
        et: float or np.array
            Input ephemeris time.

        Returns
        -------
        np.array
            SPICE quaternions of the spacecraft pointing attitude.

        """
        p = self.isis.tables['InstrumentPointing'].data
        q0 = p['J2000Q0']
        q1 = p['J2000Q1']
        q2 = p['J2000Q2']
        q3 = p['J2000Q3']
        ets = p['ET']

        p = np.array([
            np.interp(et, ets, q0),
            np.interp(et, ets, q1),
            np.interp(et, ets, q2),
            np.interp(et, ets, q3),
        ])

        return hat(p)

    @property
    def _q_inst(self):
        """Instrument rotation matrix from the spacecraft frame."""
        return m2q(np.reshape(
            self.isis.tables['InstrumentPointing']['ConstantRotation'], (3, 3)))

    @property
    def _inst_q(self):
        """Instrument boresight pointing."""
        q = q_mult(self._q_inst, self._flat(self._cassini_pointing(self.et)))
        return self._grid(q)

    @property
    def j2000(self):
        """Camera pixel pointing direction in J2000 frame."""
        if self.__j2000 is None:
            self.__j2000 = q_rot_t(self._inst_q, self.camera.pixels)
            self.__sky = None
            self.__xyz = None
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
            self.__cxyz = None
            self.__contour = None
            self.__rsky = None
            self.__rxyz = None
            self.__rlonlat = None
            self.__rlimb = None
            self.__fsky = None
            self.__fxyz = None
            self.__flonlat = None
            self.__flimb = None
            self.__spec_pix = None
            self.__spec_pts = None
            self.__spec_mid_pt = None
            self.__pixels = None
        return self.__j2000

    @property
    def sky(self):
        """Camera pixel pointing direction in J2000 frame."""
        if self.__sky is None:
            self.__sky = radec(self.j2000)
            self.__xyz = None
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
            self.__cxyz = None
            self.__contour = None
            self.__rsky = None
            self.__rxyz = None
            self.__rlonlat = None
            self.__rlimb = None
            self.__fsky = None
            self.__fxyz = None
            self.__flonlat = None
            self.__flimb = None
            self.__spec_pix = None
            self.__spec_pts = None
            self.__spec_mid_pt = None
            self.__pixels = None
        return self.__sky

    @property
    def pointing(self):
        """Mean camera pointing.

        Returns
        -------
        float, float, float
            Mean right-ascension, mean declination and fov radius (in degrees).

        """
        ra, dec = radec(self._mean(self.j2000))

        # Search FOV max diameter
        vecs = self._flat(self.j2000)
        imaxs = v_max_dist(vecs)
        fov = np.degrees(np.arccos(np.dot(vecs[:, imaxs[0]], vecs[:, imaxs[1]])))

        return ra, dec, fov / 2

    def _body_rotation(self, et):
        """Main target body rotation quaternion.

        The body rotation is extracted from
        ISIS tables and linearly interpolated on pixel
        ephemeris times.

        Note
        ----
        Quaternions should be interpolated together with
        Slerp method (see :py:func:`angles.q_interp`).
        But most of the time the drift of the pointing
        between the recorded ETs values is small enough
        to use a linear interpolation.

        Parameters
        ----------
        et: float or np.array
            Input ephemeris time.

        Returns
        -------
        np.array
            Grid (Nl, NS) of the main target body rotation
            quaternion.

        """
        p = self.isis.tables['BodyRotation'].data
        q0 = p['J2000Q0']
        q1 = p['J2000Q1']
        q2 = p['J2000Q2']
        q3 = p['J2000Q3']
        ets = p['ET']

        p = np.array([
            np.interp(et, ets, q0),
            np.interp(et, ets, q1),
            np.interp(et, ets, q2),
            np.interp(et, ets, q3),
        ])

        return hat(p)

    def _sc_position(self, et):
        """Spacecraft position in the main target body frame.

        The spacecraft position is extracted from
        ISIS tables and linearly interpolated on pixel
        ephemeris times.

        Parameters
        ----------
        et: float or np.array
            Input ephemeris time.

        Returns
        -------
        np.array
            Grid (Nl, NS) of the spacecraft J2000 position
            in the main target frame.

        """
        p = self.isis.tables['InstrumentPosition'].data
        x = p['J2000X']
        y = p['J2000Y']
        z = p['J2000Z']
        ets = p['ET']

        j2000 = np.array([
            np.interp(et, ets, x),
            np.interp(et, ets, y),
            np.interp(et, ets, z),
        ])

        return q_rot(self._body_rotation(et), j2000)

    @property
    def _xyz(self):
        """Camera pixels intersect with main target frame (ref: J2000).

        Intersection between the line-of-sight and the main target
        body.

        Note
        ----
        For now the target is considered as a sphere (not an ellipsoid)
        to provide planecentric coordinates.

        """
        if self.__xyz is None:
            v = self._flat(q_rot(self._body_rotation(self.et), self.j2000))
            sc = self._flat(self._sc_position(self.et))

            self.__xyz = self._grid(intersect(v, sc, self.target_radius))
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
            self.__cxyz = None
            self.__contour = None
            self.__rsky = None
            self.__rxyz = None
            self.__rlonlat = None
            self.__rlimb = None
            self.__fsky = None
            self.__fxyz = None
            self.__flonlat = None
            self.__flimb = None
            self.__spec_pix = None
            self.__spec_pts = None
            self.__spec_mid_pt = None
            self.__pixels = None
        return self.__xyz

    @property
    def lonlat(self):
        """Planetocentric geographic coordinates in main target frame."""
        if self.__lonlat is None:
            self.__lonlat = lonlat(self._xyz)
        return self.__lonlat

    @property
    def lon(self):
        """Planetocentric West longitude.

        Longitude in degrees between ``[0°W; 360°W[``.

        """
        return self.lonlat[0]

    @property
    def lon_e(self):
        """Planetocentric East coordinates.

        Longitude in degrees between ``]-180°E; 180°E]``.

        """
        return deg180(-self.lon)

    @property
    def lat(self):
        """Planetocentric North latitude.

        Latitude in degrees between ``[-90°N; 90°N]``.

        """
        return self.lonlat[1]

    @property
    def _dist(self):
        """Pixel distance to the main target body center."""
        return norm(self._xyz)

    @property
    def alt(self):
        """Planetocentric altitude from the main target body center."""
        if self.__alt is None:
            self.__alt = np.max([
                np.zeros((self.NL, self.NS)),
                self._dist - self.target_radius
            ], axis=0)

        return self.__alt

    @property
    def limb(self):
        """Is pixel at the limb."""
        return self.alt > 1e-6

    @property
    def ground(self):
        """Is pixel on the ground."""
        return ~self.limb

    @property
    def ground_lonlat(self):
        """Planetocentric West longitude and latitude on the ground."""
        return np.ma.array(self.lonlat, mask=[self.limb, self.limb])

    @property
    def ground_lon(self):
        """Planetocentric West longitude on the ground."""
        return np.ma.array(self.lon, mask=self.limb)

    @property
    def ground_lon_e(self):
        """Planetocentric East longitude on the ground."""
        return np.ma.array(self.lon_e, mask=self.limb)

    @property
    def ground_lat(self):
        """Planetocentric latitude on the ground."""
        return np.ma.array(self.lat, mask=self.limb)

    def _sun_position(self, et):
        """Sun position in the main target body frame.

        The sun position is extracted from
        ISIS tables and linearly interpolated on pixel
        ephemeris times.

        Parameters
        ----------
        et: float or np.array
            Input ephemeris time.

        Returns
        -------
        np.array
            Grid (Nl, NS) of the sun J2000 position
            in the main target frame.

        """
        p = self.isis.tables['SunPosition'].data
        x = p['J2000X']
        y = p['J2000Y']
        z = p['J2000Z']
        ets = p['ET']

        j2000 = np.array([
            np.interp(et, ets, x),
            np.interp(et, ets, y),
            np.interp(et, ets, z),
        ])

        return q_rot(self._body_rotation(et), j2000)

    @property
    def _illumination(self):
        """Cube local illumination angles [degrees]."""
        if self.__ill is None:
            xyz = self._flat(self._xyz)
            sc = self._flat(self._sc_position(self.et)) - xyz
            sun = self._flat(self._sun_position(self.et)) - xyz

            inc = angle(xyz, sun)
            eme = angle(xyz, sc)
            phase = angle(sc, sun)
            azi = azimuth(inc, eme, phase)
            self.__ill = self._grid(np.vstack([inc, eme, phase, azi]))
        return self.__ill

    @property
    def inc(self):
        """Cube local incidence angle [degrees]."""
        return self._illumination[0]

    @property
    def eme(self):
        """Cube local emergence angle [degrees]."""
        return self._illumination[1]

    @property
    def phase(self):
        """Cube local phase angle [degrees]."""
        return self._illumination[2]

    @property
    def azi(self):
        """Cube local azimuthal angle [degrees]."""
        return self._illumination[3]

    @property
    def ground_inc(self):
        """Incidence angle on the ground [degrees]."""
        return np.ma.array(self.inc, mask=self.limb)

    @property
    def ground_eme(self):
        """Emergence angle on the ground [degrees]."""
        return np.ma.array(self.eme, mask=self.limb)

    @property
    def ground_phase(self):
        """Phase angle on the ground [degrees]."""
        return np.ma.array(self.phase, mask=self.limb)

    @property
    def ground_azi(self):
        """Azimuthal angle on the ground [degrees]."""
        return np.ma.array(self.azi, mask=self.limb)

    @property
    def dist_sc(self):
        """Intersect point distance to the spacecraft [km]."""
        return norm(self._xyz - self._sc_position(self.et))

    @property
    def dist_sun(self):
        """Average distance to the Sun from the target body center [AU]."""
        return np.mean(norm(self._sun_position(self.et))) / AU

    @property
    def res_s(self):
        """Sample pixel resolution at the intersect point [km/pixel]."""
        return self.dist_sc * self.camera.pix_res_x

    @property
    def res_l(self):
        """Line pixel resolution at the intersect point [km/pixel]."""
        return self.dist_sc * self.camera.pix_res_y

    @property
    def res(self):
        """Pixels mean resolution at the intersect point [km/pixel]."""
        return self.dist_sc * self.camera.pix_res

    @property
    def pix_res(self):
        """Mean pixels resolution [km/pixel]."""
        return self._mean([self.res])[0]

    @property
    def ground_res_s(self):
        """Oblique pixel resolution on the ground in sample direction."""
        return np.ma.array(self.res_s / np.cos(np.radians(self.eme)), mask=self.limb)

    @property
    def ground_res_l(self):
        """Oblique pixel resolution on the ground in line direction."""
        return np.ma.array(self.res_l / np.cos(np.radians(self.eme)), mask=self.limb)

    @property
    def ground_res(self):
        """Mean oblique pixel resolution on the ground."""
        return np.ma.array(self.res / np.cos(np.radians(self.eme)), mask=self.limb)

    @property
    def v_sc(self):
        """Median sub-spacecraft position vector in main target frame."""
        return self._sc_position(self.et_median)

    @property
    def sc(self):
        """Median sub-spacecraft geographic coordinates."""
        return lonlat(self.v_sc)

    @property
    def sc_lon(self):
        """Median sub-spacecraft west longitude."""
        return self.sc[0]

    @property
    def sc_lat(self):
        """Median sub-spacecraft north latitude."""
        return self.sc[1]

    @property
    def v_ss(self):
        """Median sub-solar position vector in main target frame."""
        return self._sun_position(self.et_median)

    @property
    def ss(self):
        """Median sub-solar geographic coordinates."""
        return lonlat(self.v_ss)

    @property
    def ss_lon(self):
        """Median sub-solar west longitude."""
        return self.ss[0]

    @property
    def ss_lat(self):
        """Median sub-solar north latitude."""
        return self.ss[1]

    @property
    def ortho(self):
        """Pixel orthographic projection."""
        return ortho_proj(*self.lonlat, *self.sc, self.target_radius, self.alt)

    @property
    def ground_ortho(self):
        """Orthographic projection of the pixels on the ground."""
        return ortho_proj(self.ground_lon, self.ground_lat, *self.sc, self.target_radius)

    @property
    def fov_patch(self):
        """Mean field of view patch on the ground."""
        return great_circle_patch(*self.sc, inside=True, color='r', alpha=.1)

    @property
    def sun_patch(self):
        """Sun illumination patch on the ground."""
        return great_circle_patch(*self.ss, inside=True, color='gold', alpha=.1)

    @property
    def shadow_patch(self):
        """Shadow patch on the ground."""
        return great_circle_patch(*self.ss, inside=False, color='k', alpha=.1)

    @property
    def pixels(self):
        """Cube collection of all the pixels."""
        if self.__pixels is None:
            self.__pixels = VIMSPixels(self)
        return self.__pixels

    # ============
    # FOV CONTOUR
    # ============
    @property
    def cet(self):
        """Contour ephemeris time."""
        return np.hstack([
            self.et[0, 0],      # Top-Left corner
            self.et[0, :],      # Top edge
            self.et[0, -1],     # Top-Right corner
            self.et[:, -1],     # Right edge
            self.et[-1, -1],    # Bottom-Right corner
            self.et[-1, ::-1],  # Bottom edge
            self.et[-1, 0],     # Bottom-Left corner
            self.et[::-1, 0],   # Left edge
            self.et[0, 0],      # Top-Left corner
        ])

    @property
    def cpixels(self):
        """Camera contour pixel pointing direction in J2000 frame."""
        q = q_mult(self._q_inst, self._cassini_pointing(self.cet))
        return q_rot_t(q, self.camera.cpixels)

    @property
    def csky(self):
        """Camera contour pixel pointing direction in RA/DEC frame."""
        return radec(self.cpixels)

    @property
    def _cxyz(self):
        """Camera pixels intersect with main target frame (ref: J2000).

        Intersection between the line-of-sight and the main target
        body.

        Note
        ----
        For now the target is considered as a sphere (not an ellipsoid)
        to provide planecentric coordinates.

        """
        if self.__cxyz is None:
            et = self.cet
            v = q_rot(self._body_rotation(et), self.cpixels)
            sc = self._sc_position(et)

            self.__cxyz = intersect(v, sc, self.target_radius)
        return self.__cxyz

    @property
    def clonlat(self):
        """Planetocentric geographic contour coordinates in main target frame."""
        return lonlat(self._cxyz)

    @property
    def calt(self):
        """Planetocentric contour altitude from the main target body center."""
        dist = norm(self._cxyz)
        return np.max([
            np.zeros(np.shape(dist)), dist - self.target_radius
        ], axis=0)

    @property
    def cortho(self):
        """Pixel contour orthographic projection."""
        return ortho_proj(*self.clonlat, *self.sc, self.target_radius, self.calt)

    @property
    def ground_cortho(self):
        """Orthographic projection of the contour pixels on the ground."""
        return ortho_proj(*self.clonlat, *self.sc, self.target_radius)

    @property
    def contour(self):
        """VIMS FOV contour."""
        if self.__contour is None:
            self.__contour = VIMSContour(self)
        return self.__contour

    def in_contour(self, lon_w, lat):
        """Check if geographic point is in VIMS FOV contour."""
        return (lon_w, lat) in self.contour

    # ========
    # CORNERS
    # ========
    @property
    def ret(self):
        """Corner ephemeris time.

        Note
        ----
        Corner are defined as diagonal points
        compare to the pixel center.

        """
        return np.moveaxis(4 * [self.et], 0, 2).flatten()

    @property
    def rpixels(self):
        """Camera corner pixel pointing direction in J2000 frame.

        Corners order:
            - Top Left
            - Top Right
            - Bottom Right
            - Bottom Left

        Note
        ----
        Corner are defined as diagonal points
        compare to the pixel center.

        """
        q = q_mult(self._q_inst, self._cassini_pointing(self.ret))
        return q_rot_t(q, np.reshape(self.camera.rpixels, (3, 4 * self.NP)))

    @property
    def rsky(self):
        """Camera corner pixel pointing direction in RA/DEC frame."""
        if self.__rsky is None:
            self.__rsky = radec(self.rpixels).reshape((2, self.NL, self.NS, 4))
        return self.__rsky

    @property
    def _rxyz(self):
        """Camera pixel corners intersect with main target frame (ref: J2000).

        Intersection between the line-of-sight and the main target body.

        Note
        ----
        For now the target is considered as a sphere (not an ellipsoid)
        to provide planecentric coordinates.

        Corner are defined as diagonal points
        compare to the pixel center.

        """
        if self.__rxyz is None:
            et = self.ret
            v = q_rot(self._body_rotation(et), self.rpixels)
            sc = self._sc_position(et)

            self.__rxyz = intersect(v, sc, self.target_radius)
            self.__rlonlat = None
            self.__rlimb = None
            self.__pixels = None
        return self.__rxyz

    @property
    def rlonlat(self):
        """Planetocentric geographic corners coordinates in main target frame."""
        if self.__rlonlat is None:
            shape = (2, self.NL, self.NS, 4)
            self.__rlonlat = np.reshape(lonlat(self._rxyz), shape)
        return self.__rlonlat

    @property
    def ralt(self):
        """Planetocentric corners altitude from the main target body center."""
        dist = norm(self._rxyz)
        return np.reshape(np.max([
            np.zeros(np.shape(dist)), dist - self.target_radius
        ], axis=0), (self.NL, self.NS, 4))

    @property
    def rlimb(self):
        """Is all pixel corners are all at the limb."""
        if self.__rlimb is None:
            self.__rlimb = np.min(self.ralt > 1e-6, axis=2)
        return self.__rlimb

    @property
    def rground(self):
        """Is at least one pixel corner on the ground."""
        return ~self.rlimb

    # ==========
    # FOOTPRINT
    # ==========
    @property
    def fet(self):
        """Footprint ephemeris time.

        Note
        ----
        Footprint are set on circle or an ellipse
        based on the shape of the pixel.

        """
        return np.moveaxis(9 * [self.et], 0, 2).flatten()

    @property
    def fpixels(self):
        """Camera footprint pixel pointing direction in J2000 frame.

        Footprint order:
            - Top Left
            - Top
            - Top Right
            - Right
            - Bottom Right
            - Bottom
            - Bottom Left
            - Left
            - Top Left

        Note
        ----
        Footprint are set on circle or an ellipse
        based on the shape of the pixel.

        """
        q = q_mult(self._q_inst, self._cassini_pointing(self.fet))
        pixels = np.reshape(self.camera.fpixels, (3, 9 * self.NP))
        return q_rot_t(q, pixels)

    @property
    def fsky(self):
        """Camera footprint pixel pointing direction in RA/DEC frame."""
        if self.__fsky is None:
            self.__fsky = radec(self.fpixels).reshape((2, self.NL, self.NS, 9))
        return self.__fsky

    @property
    def _fxyz(self):
        """Camera pixel footprints intersect with main target frame (ref: J2000).

        Intersection between the line-of-sight and the main target body.

        Note
        ----
        For now the target is considered as a sphere (not an ellipsoid)
        to provide planecentric coordinates.

        Footprint are set on circle or an ellipse
        based on the shape of the pixel.

        """
        if self.__fxyz is None:
            et = self.fet
            v = q_rot(self._body_rotation(et), self.fpixels)
            sc = self._sc_position(et)

            self.__fxyz = intersect(v, sc, self.target_radius)
            self.__flonlat = None
            self.__flimb = None
            self.__pixels = None
        return self.__fxyz

    @property
    def flonlat(self):
        """Planetocentric geographic footprints coordinates in main target frame."""
        if self.__flonlat is None:
            shape = (2, self.NL, self.NS, 9)
            self.__flonlat = np.reshape(lonlat(self._fxyz), shape)
        return self.__flonlat

    @property
    def falt(self):
        """Planetocentric footprints altitude from the main target body center."""
        dist = norm(self._fxyz)
        return np.reshape(np.max([
            np.zeros(np.shape(dist)), dist - self.target_radius
        ], axis=0), (self.NL, self.NS, 9))

    @property
    def flimb(self):
        """Is all pixel footpoint points are all at the limb."""
        if self.__flimb is None:
            self.__flimb = np.min(self.falt > 1e-6, axis=2)
        return self.__flimb

    @property
    def fground(self):
        """Is at least one pixel footpoint point on the ground."""
        return ~self.flimb

    # =====
    # PLOT
    # =====
    def plot(self, *args, **kwargs):
        """Generic cube plot function."""
        return plot_cube(self, *args, ir_hr=self._is_ir_hr, **kwargs)

    def _band(self, b):
        """Get band index from value.

        Parameters
        ----------
        b: int
            VIMS channel band number.

        Returns
        -------
        int
            Nearest data index at requested band.

        Raises
        ------
        VIMSError
            If the provided band is outside the image range.

        Note
        ----
            No interpolation are implemented yet.
            Take the closest band for now.

        """
        if not (self.bands[0] <= b <= self.bands[-1]):
            raise VIMSError(f'Band `{b}` invalid. Must be '
                            f'between {self.bands[0]} and {self.bands[-1]}')

        return np.argmin(np.abs(self.bands - b))

    def _wvln(self, w):
        """Get wavelength index from value.

        Parameters
        ----------
        w: float
            Wavelength in microns.

        Returns
        -------
        int
            Nearest data index at requested wavelength.

        Raises
        ------
        VIMSError
            If the provided wavelength is outside the image range.

        Note
        ----
            No interpolation are implemented yet.
            Take the closest wavelength for now.

        """
        if not (self.wvlns[0] <= w <= self.wvlns[-1]):
            raise VIMSError(f'Wavelength `{w}` invalid. Must be '
                            f'between {self.wvlns[0]} and {self.wvlns[-1]}')

        return np.argmin(np.abs(self.wvlns - w))

    def _index(self, val):
        """Get index for band of wavelength.

        Parameters
        ----------
        val: int or float
            Data index value.

        Returns
        -------
        int
            Data image index.

        Raises
        ------
        VIMSError
            If the index is not a ``INT`` or a ``FLOAT``.

        """
        if isinstance(val, int):
            return self._band(val)

        if isinstance(val, float):
            return self._wvln(val)

        raise VIMSError('Index value must be a INT or a FLOAT')

    def _slice(self, val):
        """Get band or wavelength image from value.

        Parameters
        ----------
        val: slice
            Band of wavelength slice.

        Returns
        -------
        np.array
            Mean image over the slice.

        Raises
        ----
        NotImplementedError
            If the slice contains a step attribute.

        """
        if val.step is not None:
            raise NotImplementedError('Slice steps is not implemented')

        istart = self._index(val.start)
        istop = self._index(val.stop)

        return np.nanmean(self.data[istart:istop, :, :], axis=0)

    def _img(self, val):
        """Get data based on index value.

        Parameters
        ----------
        val: int, float or slice
            Data index value.

        Returns
        -------
        np.array
            Data image at index.

        """
        if isinstance(val, slice):
            return self._slice(val)

        return self.data[self._index(val), :, :]

    def _rgb(self, r, g, b):
        """Parse RGB self data.

        Parameters
        ----------
        r: int, float or str
            Red data index.
        g: int, float or str
            Green data index.
        b: int, float or str
            Blue data index.

        Returns
        -------
        np.array
            8 bits RGB image.

        """
        return rgb(self._img(r), self._img(g), self._img(b))

    def save(self, index, fname=None):
        """Save image plane.

        Parameters
        ----------
        index: int, float, str, tuple, list.
            Data index.
        fname: str, optional
            Output filename.

        """
        if fname is None:
            suffix = f'{index}'\
                .replace(':', '-')\
                .replace(',', '_')\
                .replace('(', '')\
                .replace(')', '')\
                .replace('\'', '')\
                .replace(' ', '')

            fname = f'{self}_{suffix}.jpg'

        save_img(fname, self[index], ir_hr=self._is_ir_hr)

    @property
    def flyby(self):
        """Cube flyby."""
        return None if self.target_name == 'SKY' else FLYBYS @ self.time

    def dist_pt(self, lon_w, lat):
        """Haversine distances between a geographic point and all the pixels."""
        return np.ma.array(
            hav_dist(lon_w, lat, self.lon, self.lat, self.target_radius),
            mask=self.limb
        )

    def get_pixel(self, lon_w, lat):
        """Get the pixel closest pixel to a specific geographic coordinate."""
        if not self.in_contour(lon_w, lat):
            return None

        # Try to find the closest pixel
        dist = self.dist_pt(lon_w, lat)
        i, j = np.unravel_index(np.argmin(dist), dist.shape)
        s, l = self._sl[:, i, j]
        pixel = self.pixels[int(s), int(l)]

        if (lon_w, lat) in pixel:
            return pixel

        # Loop over all the pixels. Exit on the first match.
        for l in range(1, self.NL + 1):
            for s in range(1, self.NS + 1):
                if (lon_w, lat) in self.pixels[s, l]:
                    return self.pixels[s, l]
        return None

    @property
    def specular_pixels(self):
        """List specular pixels."""
        if self.__spec_pix is None:
            pixels = []
            for l in range(1, self.NL + 1):
                for s in range(1, self.NS + 1):
                    pixel = self.pixels[s, l]
                    if pixel.is_specular:
                        pixels.append(pixel)
            self.__spec_pix = pixels
        return self.__spec_pix

    @property
    def specular_sl(self):
        """Specular pixels positions."""
        return np.array([[pixel.s, pixel.l] for pixel in self.specular_pixels])

    @property
    def guess_specular_pixels(self):
        """Guess if the cube has specular pixels.

        1. Take the first, mid and last specular locations
        and check if they are included in the FOV contour.

        2. Check if the specular locations for these
        three pixel fall all into the same pixel.

        """
        first = self.pixels[1, 1]
        middle = self.pixels[self.NS // 2, self.NL // 2]
        last = self.pixels[self.NS, self.NL]

        if (first.specular_lonlat not in self.contour
                and middle.specular_lonlat not in self.contour
                and last.specular_lonlat not in self.contour):
            return []

        first_pix = self.get_pixel(*first.specular_lonlat)
        middle_pix = self.get_pixel(*middle.specular_lonlat)
        last_pix = self.get_pixel(*last.specular_lonlat)

        if first_pix == middle_pix == last_pix:
            return [] if first_pix is None else [first_pix]

        return self.specular_pixels

    @property
    def nb_specular(self):
        """Number of specular pixels."""
        return len(self.specular_pixels)

    @property
    def guess_nb_specular(self):
        """Guess the number of specular pixels."""
        return len(self.guess_specular_pixels)

    @property
    def _specular_pts(self):
        """List specular point locations at the begging and end of each line."""
        if self.__spec_pts is None:
            pts = []
            for l in range(1, self.NL + 1):
                pts.append(self.pixels[1, l].specular_pt)
                pts.append(self.pixels[self.NS, l].specular_pt)
            self.__spec_pts = np.transpose(pts)
        return self.__spec_pts

    @property
    def specular_pts_lonlat(self):
        """Specular points west longitudes."""
        return self._specular_pts[:2]

    @property
    def specular_pts_lon(self):
        """Specular points west longitudes."""
        return self._specular_pts[0]

    @property
    def specular_pts_lat(self):
        """Specular points latitudes."""
        return self._specular_pts[1]

    @property
    def specular_pts_angle(self):
        """Specular points angles."""
        return self._specular_pts[2]

    @property
    def specular_pts_length(self):
        """Specular points length.

        Distance on the ground crossed by the specular points
        during the cube acquisition.

        """
        lonlat = self.specular_pts_lonlat.astype(float)
        return np.sum(hav_dist(*lonlat[:, :-1], *lonlat[:, 1:], self.target_radius))

    @property
    def specular_pts_dangle(self):
        """Specular points angular range."""
        angles = self.specular_pts_angle.astype(float)
        return np.nanmax(angles) - np.nanmin(angles)

    @property
    def specular_mid_pt(self):
        """Specular mid point."""
        if self.__spec_mid_pt is None:
            mid_pixel = self.pixels[self.NS // 2, self.NL // 2]
            angle = mid_pixel.specular_angle if mid_pixel.specular_angle else np.nan

            self.__spec_mid_pt = {
                'lonlat': mid_pixel.specular_lonlat,
                'lon': mid_pixel.specular_lon,
                'lat': mid_pixel.specular_lat,
                'angle': angle,
                'sun_a': mid_pixel.sun_footprint_a,
                'sun_b': mid_pixel.sun_footprint_b,
                'sun_area': mid_pixel.sun_footprint_area,
            }
        return self.__spec_mid_pt

    def star(self, star_obj):
        """Star object corrected from proper motion and observer position.

        Parameters
        ----------
        star_obj: dict
            Star object dictionary from stars catalog. For example:

            .. code:: python

                {
                    'source_id': 6071671369457586688,
                    'ra': 187.81968200536744,
                    'dec': -57.081421470214885,
                    'pmra': 2.3170379374019983,
                    'pmdec': -21.34892029322907,
                    'parallax': 5.621437016523866,
                    'phot_g_mean_mag': 6.3963637,
                }

        """
        return Star(et=self.et_median,
                    obs=-self._sun_position(self.et_median),  # Observer: Cassini -> Sun
                    **star_obj)

    @property
    def vis_background(self):
        """QUB VIS background in DN (NL, 96)."""
        return self.isis['SideplaneVis']['Value'].reshape(self.NL, 96)

    @property
    def ir_background(self):
        """QUB IR background in DN (NL, 256)."""
        return self.isis['SideplaneIr']['Value'].reshape(self.NL, 256)

    @property
    def qub_background(self):
        """QUB original background in DN (NL, 352)."""
        return np.c_[self.vis_background, self.ir_background]

    @property
    def _background(self):
        """Select background based on cube channel (NB, NL)."""
        return self.ir_background.T if self._is_ir else \
            self.vis_background.T

    @property
    def background(self):
        """Extrapolated background in the sample-axis (NB, NL, NS)."""
        return np.broadcast_to(
            self._background[:, :, None],
            self.shape,
        )

    def hot_pixels(self, frac=95, tol=2.5):
        """Locate hot pixel from the background.

        Parameters
        ----------
        frac: float, optional
            Apriori fraction of valid pixels (95 % by default)
        tol: flat, optional
            Detection thresold criteria (2.5 by default)

        Returns
        -------
        list
            Sorted list of the channel(s) with hot pixels.

        Raises
        ------
        NotImplementedError
            If the cube is a VISIBLE cube.

        See Also
        --------
        :py:func:`pyvims.wvlns.ir_hot_pixels`

        """
        if self._is_ir:
            return ir_hot_pixels(self._background, frac=frac, tol=tol)

        raise NotImplementedError(
            'Hot pixel detection is not implemented for the VISIBLE channel.')

    def w_hot_pixels(self, frac=95, tol=2.5):
        """Locate the wavelength of the hot pixel from the background.

        Parameters
        ----------
        frac: float, optional
            Apriori fraction of valid pixels (95 % by default)
        tol: flat, optional
            Detection thresold criteria (2.5 by default)

        Returns
        -------
        list
            Sorted list of the wavelength(s) with hot pixels.

        Raises
        ------
        NotImplementedError
            If the cube is a VISIBLE cube.

        Note
        ----
        The wavelengths of the hot pixel correspond
        to the cube wavelengths and included the
        IR-wavelength shift.

        See Also
        --------
        :py:func:`hot_pixels`

        """
        if self._is_ir:
            return self.wvlns[self.hot_pixels() - 97]

        raise NotImplementedError(
            'Hot pixel detection is not implemented for the VISIBLE channel.')
