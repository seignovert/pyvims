"""VIMS pixel module."""

from .coordinates import salt, slat, slon
from .corners import VIMSPixelCorners, VIMSPixelFootpint
from .errors import VIMSError


class VIMSPixel:
    """VIMS pixel object.

    Parameters
    ----------
    cube: pyvims.VIMS
        Parent VIMS cube.
    s: int
        Sample position (``1`` to ``NS``).
    l: int
        Line position (``1`` to ``NL``).

    """

    def __init__(self, cube, s, l):
        self._cube = cube
        self.s = s
        self.l = l

    def __str__(self):
        return f'{self._cube}-S{self.s}_L{self.l}'

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> {self}',
            f'Sample: {self.s}',
            f'Line: {self.l}',
            f'Lon: {self.slon}',
            f'Lat: {self.slat}',
            f'Alt: {self.salt}',
        ])

    def __getitem__(self, val):
        if isinstance(val, (int, float, str, slice)):
            return self._cube[val][self.j, self.i]

        raise VIMSError('\n - '.join([
            f'Invalid format. Use:',
            'INT -> Band image',
            'FLOAT -> Wavelength image',
        ]))

    def __matmul__(self, val):
        return self[val]

    def __contains__(self, item):
        """Check the item is inside the pixel.

        Parameters
        -----------
        item: (float, float)
            Geographic point: ``(west_longitude, latitude)``

        Note
        ----
        By default, the intersection is calculated based on the pixel
        corners polygon projected on the ground (using a Lambert
        azimuthal equal-area projection).

        Intersection can be also calculated directly on the
        :py:attr:`corners` and :py:attr:`footprint` attributes.

        """
        return item in self.corners

    @property
    def s(self):
        """Pixel sample position."""
        return self.__s

    @s.setter
    def s(self, sample):
        """Sample value setter.

        Raises
        ------
        VIMSError
            If the sample is outside the image range.

        """
        if not isinstance(sample, int):
            raise VIMSError(f'Sample `{sample}` must be an integer.')

        if not 1 <= sample <= self._cube.NS:
            raise VIMSError(
                f'Sample `{sample}` invalid. Must be between 1 and {self._cube.NS}')

        self.__s = sample

    @property
    def i(self):
        """Sample index value."""
        return self.s - 1

    @property
    def l(self):
        """Pixel lines position."""
        return self.__l

    @l.setter
    def l(self, line):
        """Line value setter.

        Raises
        ------
        VIMSError
            If the line is outside the image range.

        """
        if not isinstance(line, int):
            raise VIMSError(f'Line `{line}` must be an integer.')

        if not 1 <= line <= self._cube.NL:
            raise VIMSError(
                f'Line `{line}` invalid. Must be between 1 and {self._cube.NL}')

        self.__l = line

    @property
    def j(self):
        """Line index value."""
        return self.l - 1

    @property
    def wvlns(self):
        """Pixel central wavelengths (µm)."""
        return self._cube.wvlns

    @property
    def spectrum(self):
        """Get pixel spectrum.

        Returns
        -------
        np.array
            Spectrum at (S, L).

        """
        return self._cube.data[:, self.j, self.i]

    @property
    def et(self):
        """Pixel ephemeris time."""
        return self._cube.et[self.j, self.i]

    @property
    def j2000(self):
        """Pixel pointing direction in J2000 frame."""
        return self._cube.pixels[:, self.j, self.i]

    @property
    def ra(self):
        """Pixel right ascension (deg)."""
        return self._cube.sky[0, self.j, self.i]

    @property
    def dec(self):
        """Pixel right declination (deg)."""
        return self._cube.sky[1, self.j, self.i]

    @property
    def lonlat(self):
        """Pixel West longitude and latitude (deg)."""
        return self._cube.lonlat[:, self.j, self.i]

    @property
    def lon(self):
        """Pixel West longitude (deg)."""
        return self._cube.lon[self.j, self.i]

    @property
    def lon_e(self):
        """Pixel East longitude (deg)."""
        return self._cube.lon_e[self.j, self.i]

    @property
    def slon(self):
        """Pixel longitude as string."""
        return slon(self.lon)

    @property
    def lat(self):
        """Pixel latitude (deg)."""
        return self._cube.lat[self.j, self.i]

    @property
    def slat(self):
        """Pixel latitude as string."""
        return slat(self.lat)

    @property
    def limb(self):
        """Pixel is at the limb."""
        return self._cube.limb[self.j, self.i]

    @property
    def ground(self):
        """Pixel is on the ground."""
        return ~self.limb

    @property
    def alt(self):
        """Pixel altitude (km)."""
        return 0 if self.ground else self._cube.alt[self.j, self.i]

    @property
    def salt(self):
        """Pixel altitude string."""
        return f'{salt(self.alt)} ({"Limb" if self.limb else "Ground"} pixel)'

    @property
    def inc(self):
        """Pixel local incidence angle (degrees)."""
        return self._cube.inc[self.j, self.i]

    @property
    def eme(self):
        """Pixel local emergence angle (degrees)."""
        return self._cube.eme[self.j, self.i]

    @property
    def phase(self):
        """Pixel local phase angle (degrees)."""
        return self._cube.phase[self.j, self.i]

    @property
    def dist_sc(self):
        """Intersect point distance to the spacecraft."""
        return self._cube.dist_sc[self.j, self.i]

    @property
    def res_s(self):
        """Sample pixel resolution at the intersect point."""
        return self._cube.res_s[self.j, self.i]

    @property
    def res_l(self):
        """Line pixel resolution at the intersect point."""
        return self._cube.res_l[self.j, self.i]

    @property
    def res(self):
        """Pixel mean resolution at the intersect point."""
        return self._cube.res[self.j, self.i]

    @property
    def is_specular(self):
        """Calculate if the specular point is within the pixel."""
        return self._cube.is_specular[self.j, self.i] if self.ground else None

    @property
    def specular_lon(self):
        """Specular point west longitude location."""
        return self._cube.specular_lon[self.j, self.i] if self.ground else None

    @property
    def specular_lat(self):
        """Specular point north latitude location."""
        return self._cube.specular_lat[self.j, self.i] if self.ground else None

    @property
    def specular_angle(self):
        """Specular point north latitude location."""
        return self._cube.specular_angle[self.j, self.i] if self.ground else None

    @property
    def specular_dist(self):
        """Haversine distance between the pixel and the specular reflection."""
        return self._cube.specular_dist[self.j, self.i] if self.ground else None

    @property
    def corners(self):
        """VIMS pixel corners."""
        return VIMSPixelCorners(self)

    @property
    def footprint(self):
        """VIMS pixel footprint."""
        return VIMSPixelFootpint(self)

    def plot(self, **kwargs):
        """Plot spectrum."""
        self._cube.plot((self.s, self.l), **kwargs)
