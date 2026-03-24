"""Angles module."""

import re

import numpy as np


class Angle(float):
    """Angle generic object.

    Parameters
    ----------
    value: float
        Input angle value.

    """

    def __add__(self, other):
        return self.__class__(float(self) + other)

    def __radd__(self, other):
        return self.__class__(other + float(self))

    def __sub__(self, other):
        return self.__class__(float(self) - other)

    def __rsub__(self, other):
        return self.__class__(other - float(self))

    @staticmethod
    def rint(value, dec=9):
        """Rounded integer.

        Parameters
        ----------
        value: int or float
            Input value to round.
        dec: int, optional
            Rounding precision decimals.

        """
        return int(round(value, dec))

    @property
    def minutes(self):
        """Angle in decimal minutes."""
        raise NotImplementedError

    @property
    def m(self):
        """Angle in minutes."""
        return self.rint(self.minutes)

    @property
    def secondes(self):
        """Angle in decimal secondes."""
        raise NotImplementedError

    @property
    def s(self):
        """Angle in secondes."""
        return self.rint(self.secondes)

    @property
    def radians(self):
        """Angle value in radians."""
        return np.radians(float(self))

    @property
    def rad(self):
        """Angle value in radians shortcut."""
        return self.radians

    @property
    def cos(self):
        """Cosine value for the angle."""
        return np.cos(self.rad)

    @property
    def sin(self):
        """Sinus value for the angle."""
        return np.sin(self.rad)


class RA(Angle):
    """Right ascension angle object.

    Parameters
    ----------
    value: float or str
        Input angle as degree float or as HMS string.

    """

    RE_HMS = re.compile(r'(\d+)[h\s:](\d+)[m\s:](\d+\.\d+|\d+)s?')

    def __new__(cls, value):
        """Create new right ascension object from float or string."""
        v = value % 360 if not isinstance(value, str) else cls.parse(value)
        return float.__new__(cls, v)

    def __str__(self):
        return self.hms

    @property
    def hours(self):
        """Angle in decimal hours."""
        return self / 360 * 24

    @property
    def h(self):
        """Angle in hours."""
        return self.rint(self.hours)

    @property
    def minutes(self):
        """Angle in decimal minutes."""
        return (self.hours - self.h) * 60

    @property
    def secondes(self):
        """Angle in decimal secondes."""
        return (self.hours - self.h - self.m / 60) * 3600

    @property
    def hms(self):
        """Hours minutes secondes string."""
        return f'{self.h:02d}h{self.m:02d}m{self.secondes:.3f}s'

    @classmethod
    def parse(cls, hms):
        """Parse HMS string in float degree.

        Parameters
        ----------
        hms: str
            HMS string to parse. Accepted formats:
            - 12h34m56s
            - 12h34m56.789s
            - 12:34:56
            - 12:34:56.789
            - 12 34 56
            - 12 34 56.789

        Returns
        -------
        float
            Parsed HMS string as degree float.

        Raises
        ------
        ValueError
            If the input string does not fit the HMS format.

        """
        _hms = cls.RE_HMS.search(hms)
        if _hms:
            h, m, s = _hms.groups()
            deg = (int(h) + int(m) / 60 + float(s) / 3600) / 24 * 360
            return round(deg, 9)

        raise ValueError(f'Invalid HMS string: `{hms}`')


class DEC(Angle):
    """Declination angle object.

    Parameters
    ----------
    value: float or str
        Input angle as degree float or as DMS string.

    Raises
    ------
    ValueError
        If the provided value is not in [-90°, 90°].

    """

    RE_DMS = re.compile(r'[+-]?(\d+)[d\s:°º](\d+)[m\s:\'′](\d+\.\d+|\d+)[s\'\"″]?\'?')

    def __new__(cls, value):
        """Create new declination object from float or string."""
        v = value if not isinstance(value, str) else cls.parse(value)

        if v > 90:
            raise ValueError(f'Declination angle must be lower than 90°: `{v}`')
        if v < -90:
            raise ValueError(f'Declination angle must be larger than -90°: `{v}`')

        return float.__new__(cls, v)

    def __str__(self):
        return self.dms

    @property
    def degrees(self):
        """Angle in decimal degrees."""
        return abs(float(self))

    @property
    def d(self):
        """Angle in degrees."""
        return self.rint(self.degrees)

    @property
    def sign(self):
        """Angle in degree sign."""
        return '+' if float(self) >= 0 else '-'

    @property
    def minutes(self):
        """Angle in decimal minutes."""
        return abs(self.degrees - self.d) * 60

    @property
    def secondes(self):
        """Angle in decimal secondes."""
        return abs(self.degrees - self.d - self.m / 60) * 3600

    @property
    def dms(self):
        """Degrees minutes secondes string."""
        return f'{self.sign}{self.d:02d}°{self.m:02d}′{self.secondes:.3f}″'

    @classmethod
    def parse(cls, dms):
        """Parse DMS string in float degree.

        Parameters
        ----------
        dms: str
            DMS string to parse. Accepted formats:
            - 12d34m56s
            - 12d34m56.789s
            - +12d34m56s
            - -12d34m56s
            - 12:34:56
            - 12:34:56.789
            - 12 34 56
            - 12 34 56.789
            - 12°34'56'' (unicode degree and double single quote)
            - 12º34'56" (macOS degree and double quote)
            - 12°34′56″ (unicode degree, single and double prime)

        Returns
        -------
        float
            Parsed DMS string as degree float.

        Raises
        ------
        ValueError
            If the input string does not fit the DMS format.

        """
        _dms = cls.RE_DMS.search(dms)
        if _dms:
            d, m, s = _dms.groups()
            deg = int(d) + int(m) / 60 + float(s) / 3600
            deg *= -1 if dms[0] == '-' else 1
            return round(deg, 9)

        raise ValueError(f'Invalid DMS string: `{dms}`')
