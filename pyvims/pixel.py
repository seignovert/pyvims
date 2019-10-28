"""VIMS pixel module."""

import numpy as np

from .coordinates import salt, slat, slon
from .corners import VIMSPixelCorners, VIMSPixelFootpint
from .errors import VIMSError
from .specular import specular_footprint, specular_location
from .vectors import hav_dist, lonlat


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
        self.__spec = None
        self.__sun_footprint = None

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

    def __eq__(self, item):
        try:
            return str(self) == str(item)
        except TypeError:
            return False

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
    def sc_pt(self):
        """Pixel sub-spacecraft point location."""
        return self._cube._sc_position(self.et)

    @property
    def sc(self):
        """Pixel sub-spacecraft point geographic coordinates."""
        return lonlat(self.sc_pt)

    @property
    def ss_pt(self):
        """Pixel sub-solar point location."""
        return self._cube._sun_position(self.et)

    @property
    def ss(self):
        """Pixel sub-solar point geographic coordinates."""
        return lonlat(self.ss_pt)

    @property
    def target_radius(self):
        """Pixel target radius (km)."""
        return self._cube.target_radius

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

    def patch(self, **kwargs):
        """Ground corners matplotlib patch."""
        return self.corners.patch(**kwargs)

    @property
    def area(self):
        """Ground corners surface area (km^2)."""
        return self.corners.area

    @property
    def specular_pt(self):
        """Specular point location at the time of the pixel acquisition."""
        if self.__spec is None:
            self.__spec = specular_location(self.sc_pt,
                                            self.ss_pt,
                                            self.target_radius)
        return self.__spec

    @property
    def specular_lonlat(self):
        """Specular point west longitude and latitude location."""
        return self.specular_pt[:2]

    @property
    def specular_lon(self):
        """Specular point west longitude location."""
        return self.specular_pt[0]

    @property
    def specular_lat(self):
        """Specular point north latitude location."""
        return self.specular_pt[1]

    @property
    def specular_angle(self):
        """Specular point north latitude location."""
        return self.specular_pt[2]

    @property
    def is_specular(self):
        """Calculate if the specular point is within the pixel."""
        return False if self.limb or self.specular_angle is None \
            else self.specular_lonlat in self

    @property
    def specular_dist(self):
        """Haversine distance between the pixel and the specular reflection."""
        return None if not self.specular_angle else hav_dist(*self.lonlat,
                                                             *self.specular_lonlat,
                                                             self.target_radius)

    @property
    def sun_footprint(self):
        """Specular footprint of the sun at the time of the pixel acquisition."""
        if self.__sun_footprint is None:
            self.__sun_footprint = specular_footprint(self.sc_pt,
                                                      self.ss_pt,
                                                      self.target_radius)
        return self.__sun_footprint

    @property
    def _sun_footprint_r(self):
        """Specular footprint radius extent on the ground (km)."""
        return hav_dist(*self.sun_footprint,
                        *self.specular_lonlat,
                        self.target_radius)

    @property
    def sun_footprint_a(self):
        """Specular footprint max extent (km)."""
        return self._sun_footprint_r.max()

    @property
    def sun_footprint_b(self):
        """Specular footprint min extent (km)."""
        return self._sun_footprint_r.min()

    @property
    def sun_footprint_area(self):
        """Specular footprint area extent (km^2)."""
        return np.pi * self.sun_footprint_a * self.sun_footprint_b
