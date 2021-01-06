"""VIMS flyby module."""

from datetime import datetime as dt
from datetime import timezone

import numpy as np

from .vars import ROOT_DATA


class MetaFlybys(type):
    """Metaclass for the Cassini flybys."""

    CSV = ROOT_DATA / 'flybys.csv'

    __flybys = None

    def __contains__(cls, other):
        return other in cls.flybys

    def __getitem__(cls, key):
        if key not in cls:
            return None

        for flyby in cls.flybys:
            if key == flyby:
                return flyby

    def __matmul__(cls, t):
        """Get the closest."""
        if isinstance(t, str):
            t = dt.strptime(t, '%Y-%m-%dT%H:%M:%S.%f')

        delta_t = []
        for flyby in cls.flybys:
            delta_t.append(np.abs(flyby - t))

        return cls.flybys[np.argmin(delta_t)]

    @property
    def flybys(cls):
        """List if all the flybys."""
        if cls.__flybys is None:
            cls.__flybys = cls._load()
        return cls.__flybys

    @property
    def _is_file(cls):
        """Check if the flybys csv file exist."""
        return cls.CSV.exists()

    @classmethod
    def _load(cls):
        """Load the list of all the flybys."""
        if not cls._is_file:
            raise FileNotFoundError(f'Flybys data list not found in {cls.CSV.name}')

        flybys = []
        with cls.CSV.open() as f:
            for flyby in f.readlines()[1:]:
                flybys.append(Flyby(flyby))

        return flybys


class FLYBYS(metaclass=MetaFlybys):
    """List of all the Cassini flybys."""


class Flyby:
    """VIMS flyby object.

    Parameters
    ----------
    data: str
        Input data from csv file.

    """

    def __init__(self, data):
        self.__data = data.split(', ')

    def __str__(self):
        return self.name if not self.targeted else self.targeted

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> {self.name}',
            f'Target: {self.satellite}',
            f'Targeted: {self.targeted}',
            f'CA time: {self.ca}',
            f'CA altitude: {self.alt} km',
        ])

    def __eq__(self, other):
        if other.upper() == self.name:
            return True

        if self.targeted:
            return other.upper() == self.targeted

        return False

    def __sub__(self, other):
        return (
            self.ca.replace(tzinfo=timezone.utc) - other.replace(tzinfo=timezone.utc)
        ).total_seconds()

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError(f"'<' not supported between instances "
                            f"of '{type(self)}' and '{type(other)}'")
        return self.ca < other.ca

    @property
    def rev(self):
        return int(self.__data[0])

    @property
    def name(self):
        return self.__data[1]

    @property
    def targeted(self):
        return False if not self.__data[2] else self.__data[2].upper()

    @property
    def satellite(self):
        return self.__data[3].upper()

    @property
    def ca(self):
        return dt.strptime(self.__data[4], '%Y-%b-%d %H:%M')

    @property
    def doy(self):
        return int(self.__data[5])

    @property
    def alt(self):
        return int(self.__data[6])

    @property
    def in_out(self):
        return self.__data[7]

    @property
    def speed_km_s(self):
        return float(self.__data[8])

    @property
    def phase_deg(self):
        return int(self.__data[9])
