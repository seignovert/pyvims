"""Star module."""

import numpy as np

from .angles import DEC, RA
from .vectors import hat, radec, xyz


AU = 1.495978707e8     # 1 Astronomical Unit in [km]
YR = 86400 * 365.2425  # Number of seconds per years
MAS = 1 / 3600e3       # Convert [mas] to [deg]


class Star:
    """Star object seen by distant observer.

    Parameters
    ----------
    ra: float or str
        Star right ascension in J2000 frame (degree or HMS).
    dec: float or str
        Star declination in J2000 frame (degree or DMS).
    pmra: float, optional
        Star right ascension proper motion in J2000 frame (mas/yr).
    pmdec: float, optional
        Star declination proper motion in J2000 frame (mas/yr).
    et: float, optional
        Ephemeris Time or number of seconds since 2000.
    parallax: float, optional
        Star parallax (mas).
    obs: [float, float, float]
        Observer position in the J2000 frame.
    source_id: str, optional
        Star name or ID.
    epoch: str

    """

    def __init__(self, ra=0, dec=0, pmra=None, pmdec=None, et=None,
                 parallax=None, obs=None, source_id=None, epoch='J2000', **kwargs):
        self.ra_2000 = RA(ra)
        self.dec_2000 = DEC(dec)
        self.pmra = pmra
        self.pmdec = pmdec
        self.et = et
        self.parallax = parallax
        self.obs = obs
        self.source_id = source_id
        self.epoch = float(epoch.replace('J', ''))
        self.__kwargs = kwargs
        self.__radec = None

    def __str__(self):
        return '' if self.source_id is None else str(self.source_id)

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> {self}',
            f'RA: {self.ra}',
            f'DEC: {self.dec}',
            f'ET: {self.et:.0f}',
            f'Observer: {self.obs} in J2000',
        ])

    @property
    def radec_2000(self):
        """Original star coordinate not corrected from proper motion."""
        return self.ra_2000, self.dec_2000

    @property
    def dyr(self):
        """Decimal years since 2000."""
        return 0 if self.et is None else self.et / YR + 2000 - self.epoch

    @property
    def mu_ra(self):
        """Star right ascension offset since Epoch (deg)."""
        return 0 if self.pmra is None else self.dyr * self.pmra * MAS

    @property
    def mu_dec(self):
        """Star declination offset since Epoch (deg)."""
        return 0 if self.pmdec is None else self.dyr * self.pmdec * MAS

    @property
    def ra_et(self):
        """Star right ascension corrected from proper motion at ET."""
        return RA(self.ra_2000 + self.mu_ra)

    @property
    def dec_et(self):
        """Star declination corrected from proper motion at ET."""
        return DEC(self.dec_2000 + self.mu_dec)

    @property
    def radec_et(self):
        """Star coordinate corrected from proper motion at ET."""
        return self.ra_et, self.dec_et

    @property
    def dist(self):
        """Star distance in km."""
        return None if self.parallax is None else AU / np.radians(self.parallax * MAS)

    @property
    def xyz(self):
        """Star pointing vector at ET in J2000 frame."""
        return None if self.parallax is None else xyz(-self.ra_et, self.dec_et, self.dist)

    @property
    def radec(self):
        """Star apparent coordinates seen by VIMS."""
        if self.__radec is None:
            self.__radec = self.radec_et if self.parallax is None or self.obs is None \
                else radec(hat(self.xyz - self.obs))
        return self.__radec

    @property
    def ra(self):
        """Star apparent right ascension seen by VIMS."""
        return RA(self.radec[0])

    @property
    def dec(self):
        """Star apparent declination seen by VIMS."""
        return DEC(self.radec[1])
