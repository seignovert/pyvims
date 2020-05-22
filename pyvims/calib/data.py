"""VIMS calibration data module.

Source: https://pds-imaging.jpl.nasa.gov/data/cassini/cassini_orbiter/vims-calibration-files/vims-pipeline-RC19-files-2018/  # noqa:501

"""

import numpy as np

from .vars import DATA, RC
from ..interp import lin_interp
from ..pds.times import dyear


class VIMSCalibData(type):
    """Abstract VIMS data."""
    name = None
    __vis = None
    __ir = None

    def __str__(cls):
        return cls.__name__

    def __repr__(cls):
        return f'<{cls.__class__.__name__}> {cls}'

    def __call__(cls, year, vis=False):
        if hasattr(year, 'channel'):
            vis = year.channel == 'VIS'

        if hasattr(year, 'start'):
            year = dyear(year.start)

        years, data = cls.vis if vis else cls.ir

        return lin_interp(year, years, data)

    def csv(cls, vis=False):
        """Calibration multiplier data file."""
        return DATA / f'{RC}-VIMS_{"VIS" if vis else "IR"}-{cls.name}.csv'

    @property
    def vis(cls):
        """Visible multiplier factors."""
        if cls.__vis is None:
            cls.__vis = cls._load_data(vis=True)
        return cls.__vis

    @property
    def ir(cls):
        """Infrared multiplier factors."""
        if cls.__ir is None:
            cls.__ir = cls._load_data(vis=False)
        return cls.__ir

    def _load_data(cls, vis=False):
        """Load csv data."""
        years, *data = np.loadtxt(cls.csv(vis=vis), delimiter=', ', unpack=True)
        return years, data


class Multiplier(metaclass=VIMSCalibData):
    """VIMS calibration multiplier."""
    name = 'calibration_multiplier'


class SolarFlux(metaclass=VIMSCalibData):
    """VIMS calibration solar flux."""
    name = 'solar'

class Efficiency(metaclass=VIMSCalibData):
    """VIMS calibration efficiency (photon calibration)."""
    name = 'wave_photon_cal'

class Wavelengths(metaclass=VIMSCalibData):
    """VIMS calibration wavelengths."""
    name = 'wavelengths'
