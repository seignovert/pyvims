"""Read VIMS data from ISIS file."""

import os
import re

import numpy as np

from .camera import VIMSCamera
from .errors import VIMSError
from .img import rgb, save_img
from .isis import ISISCube
from .plot import plot_cube
from .projection import ortho
from .quaternions import m2q, q_mult, q_rot, q_rot_t
from .target import intersect
from .time import hex2double
from .vectors import angle, deg180, hat, lonlat, norm, radec, v_max_dist


def get_img_id(fname):
    """Extract image ID from filename.

    Parameters
    ----------
    fname:

    """
    img_ids = re.findall(r'^(?:C|v)?\d{10}_\d+(?:_\d+)?', fname)

    if not img_ids:
        raise VIMSError(f'File `{fname}` name does not '
                        'match the correct ID pattern.')

    return img_ids[0]


def _parse(val):
    """Parse index values based on type or format."""
    if isinstance(val, (int, float, slice)):
        return val

    if isinstance(val, (tuple, list)):
        values = ()
        for v in val:
            values += (_parse(v),)
        return values

    if isinstance(val, str):
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

    def __getitem__(self, val):
        val = _parse(val)

        if isinstance(val, (int, float, slice)):
            return self._img(val)

        if isinstance(val, tuple):
            if len(val) == 2:
                return self._spec(*val)

            if len(val) == 3:
                return self._rgb(*val)

        raise VIMSError('\n - '.join([
            f'Invalid format. Use:',
            'INT -> Band image',
            'FLOAT -> Wavelength image',
            '[INT, INT] -> Sample, Line spectrum',
            '[INT, INT, INT] -> Bands RGB',
            '[FLOAT, FLOAT, FLOAT] -> Wavelengths RGB',
        ]))

    def __matmul__(self, val):
        return self[val]

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
        self.__xyz = None
        self.__lonlat = None
        self.__alt = None
        self.__ill = None
        self.__cxyz = None

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
        b = self.bands
        bi = [b[k * self.NB // 6 - 1] for k in range(1, 6)]
        return [b[0], *bi, b[-1]]

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
            self.__pixels = None
            self.__sky = None
            self.__xyz = None
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
        return self.__camera

    def _cassini_pointing(self, et):
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
    def _inst_rot(self):
        """Instrument rotation matrix from the spacecraft frame."""
        return np.reshape(
            self.isis.tables['InstrumentPointing']['ConstantRotation'], (3, 3))

    @property
    def _inst_q(self):
        """Instrument boresight pointing."""
        q = q_mult(m2q(self._inst_rot), self._flat(self._cassini_pointing(self.et)))
        return self._grid(q)

    @property
    def pixels(self):
        """Camera pixel pointing direction in J2000 frame."""
        if self.__pixels is None:
            self.__pixels = q_rot_t(self._inst_q, self.camera.pixels)
            self.__sky = None
            self.__xyz = None
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
        return self.__pixels

    @property
    def sky(self):
        """Camera pixel pointing direction in J2000 frame."""
        if self.__sky is None:
            self.__sky = radec(self.pixels)
            self.__xyz = None
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
        return self.__sky

    @property
    def pointing(self):
        """Mean camera pointing.

        Returns
        -------
        float, float, float
            Mean right-ascension, mean declination and fov radius (in degrees).

        """
        ra, dec = radec(self._mean(self.pixels))

        # Search FOV max diameter
        vecs = self._flat(self.pixels)
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
        to use a linerar interpolation.

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
        """Camera pixels intersect with main traget frame (ref: J2000).

        Intersection between the line-of-sight and the main target
        body.

        Note
        ----
        For now the target is considered as a sphere (not an ellipsoid)
        to provide planecentric coordinates.

        """
        if self.__xyz is None:
            v = self._flat(q_rot(self._body_rotation(self.et), self.pixels))
            sc = self._flat(self._sc_position(self.et))

            self.__xyz = self._grid(intersect(v, sc, self.target_radius))
            self.__lonlat = None
            self.__alt = None
            self.__ill = None
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

        Longitude in degrees between ``[0ºW; 360ºW[``.

        """
        return self.lonlat[0]

    @property
    def lon_e(self):
        """Planetocentric East coordinates.

        Longitude in degrees between ``]-180ºE; 180ºE]``.

        """
        return deg180(-self.lon)

    @property
    def lat(self):
        """Planetocentric North latitude.

        Latitude in degrees between ``[-90ºN; 90ºN]``.

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
        """Cube local illumination angles (degrees)."""
        if self.__ill is None:
            xyz = self._flat(self._xyz)
            sc = self._flat(self._sc_position(self.et)) - xyz
            sun = self._flat(self._sun_position(self.et)) - xyz

            inc = angle(xyz, sun)
            eme = angle(xyz, sc)
            phase = angle(sc, sun)
            self.__ill = self._grid(np.vstack([inc, eme, phase]))
        return self.__ill

    @property
    def inc(self):
        """Cube local incidence angle (degrees)."""
        return self._illumination[0]

    @property
    def eme(self):
        """Cube local emergence angle (degrees)."""
        return self._illumination[1]

    @property
    def phase(self):
        """Cube local phase angle (degrees)."""
        return self._illumination[2]

    @property
    def ground_inc(self):
        """Incidence angle on the ground (degrees)."""
        return np.ma.array(self.inc, mask=self.limb)

    @property
    def ground_eme(self):
        """Emergence angle on the ground (degrees)."""
        return np.ma.array(self.eme, mask=self.limb)

    @property
    def ground_phase(self):
        """Phase angle on the ground (degrees)."""
        return np.ma.array(self.phase, mask=self.limb)

    @property
    def _dist_sc(self):
        """Intersect point distance to the spacecraft."""
        return norm(self._xyz - self._sc_position(self.et))

    @property
    def res_s(self):
        """Sample pixel resolution at the intersect point."""
        return self._dist_sc * self.camera.pix_res_x

    @property
    def res_l(self):
        """Line pixel resolution at the intersect point."""
        return self._dist_sc * self.camera.pix_res_y

    @property
    def res(self):
        """Pixels mean resolution at the intersect point."""
        return self._dist_sc * self.camera.pix_res

    @property
    def pix_res(self):
        """Mean pixels resolution (km/pixel)."""
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
        """Mean sub-spacecraft position vector in main target frame."""
        return self._mean(self._sc_position(self.et))

    @property
    def sc(self):
        """Mean sub-spacecraft geographic coordinates."""
        return lonlat(self.v_sc)

    @property
    def sc_lon(self):
        """Mean sub-spacecraft west longitude."""
        return self.sc[0]

    @property
    def sc_lat(self):
        """Mean sub-spacecraft north latitude."""
        return self.sc[1]

    @property
    def v_ss(self):
        """Mean sub-solar position vector in main target frame."""
        return self._mean(self._sun_position(self.et))

    @property
    def ss(self):
        """Mean sub-solar geographic coordinates."""
        return lonlat(self.v_ss)

    @property
    def ss_lon(self):
        """Mean sub-solar west longitude."""
        return self.ss[0]

    @property
    def ss_lat(self):
        """Mean sub-solar north latitude."""
        return self.ss[1]

    @property
    def ortho(self):
        """Pixel orthographic projection."""
        return ortho(*self.lonlat, *self.sc, self.target_radius, self.alt)

    @property
    def ground_ortho(self):
        """Orthographic projection of the pixels on the ground."""
        return ortho(self.ground_lon, self.ground_lat, *self.sc, self.target_radius)

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
        q = q_mult(m2q(self._inst_rot), self._cassini_pointing(self.cet))
        return q_rot_t(q, self.camera.cpixels)

    @property
    def csky(self):
        """Camera contour pixel pointing direction in J2000 frame."""
        return radec(self.cpixels)

    @property
    def _cxyz(self):
        """Camera pixels intersect with main traget frame (ref: J2000).

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
        return ortho(*self.clonlat, *self.sc, self.target_radius, self.calt)

    @property
    def ground_cortho(self):
        """Orthographic projection of the contour pixels on the ground."""
        return ortho(*self.clonlat, *self.sc, self.target_radius)

    def plot(self, *args, **kwargs):
        """Generic cube plot function."""
        return plot_cube(self, *args, **kwargs)

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

    def _spec(self, S, L):
        """Get spectrum data.

        Parameters
        ----------
        S: int
            Sample position (``1`` to ``NS``).
        L: int
            Line position (``1`` to ``NL``).

        Returns
        -------
        np.array
            Sprectrum at (S, L).

        Raises
        ------
        VIMSError
            If the sample or line provided are outside the image range.

        """
        if not isinstance(S, int):
            raise VIMSError(f'Sample `{S}` must be an integer')

        if not isinstance(L, int):
            raise VIMSError(f'Line `{L}` must be an integer')

        if not (1 <= L <= self.NL):
            raise VIMSError(
                f'Line `{L}` invalid. Must be between 1 and {self.NL}')

        if not (1 <= S <= self.NS):
            raise VIMSError(
                f'Sample `{S}` invalid. Must be between 1 and {self.NS}')

        return self.data[:, L - 1, S - 1]

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

        save_img(fname, self[index])
