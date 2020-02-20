"""Stereographic projection module."""

import numpy as np

from .__main__ import Projection
from ..angles import DEC, RA


class Sky(Projection):
    """Stereographic projection object.

    Parameters
    ----------
    ra: float, optional
        Center west longitude.
    dec: float, optional
        Center latitude (North Pole by default).
    twist: float, optional
        Planet name.

    Source
    ------
    https://proj.org/operations/projections/stere.html
    https://github.com/proj4js/proj4js/blob/master/lib/projections/stere.js

    """

    def __init__(self, ra=0, dec=0, twist=0):
        self.ra = ra
        self.dec = dec
        self.twist = twist

    def __repr__(self):
        return (f'<{self}> '
                f'RA: {self.ra}° | '
                f'Dec: {self.dec}° | '
                f'Twist: {self.twist}°')

    @property
    def ra(self):
        """Pointing right-ascension (degree)."""
        return self.__ra

    @ra.setter
    def ra(self, ra):
        """Set pointing right-ascension (degree)."""
        self.__ra = RA(ra)
        self.__cra, self.__sra = self._cs(self.__ra)
        self.__m = None

    @property
    def dec(self):
        """Pointing declination."""
        return self.__dec

    @dec.setter
    def dec(self, dec):
        """Set pointing declination (degree)."""
        self.__dec = DEC(dec)
        self.__cdec, self.__sdec = self._cs(self.__dec)
        self.__m = None

    @property
    def twist(self):
        """Pointing fov twist clockwise angle."""
        return self.__twist

    @twist.setter
    def twist(self, twist):
        """Set pointing FOV twist clockwise-angle (degree)."""
        self.__twist = twist
        self.__ctwist, self.__stwist = self._cs(self.__twist / 2)
        self.__m = None

    @property
    def pointing(self):
        """FOV pointing angles."""
        return self.ra, self.dec, self.twist

    @property
    def m(self):
        """Sky rotation matrix."""
        if self.__m is None:
            self.__m = self._rot_sky()
        return self.__m

    def _rot_sky(self):
        """Calculate the sky rotation matrix."""
        m1 = np.array([
            [self.__cdec, 0, self.__sdec],
            [0, 1, 0],
            [-self.__sdec, 0, self.__cdec],
        ])

        m2 = np.array([
            [self.__cra, self.__sra, 0],
            [-self.__sra, self.__cra, 0],
            [0, 0, 1],
        ])

        q0 = self.__ctwist
        q1 = self.__stwist * self.__cdec * self.__cra
        q2 = self.__stwist * self.__cdec * self.__sra
        q3 = self.__stwist * self.__sdec

        m3 = np.array([[
            1 - 2 * (q2 * q2 + q3 * q3),
            2 * (q1 * q2 + q0 * q3),
            2 * (q1 * q3 - q0 * q2),
        ], [
            2 * (q1 * q2 - q0 * q3),
            1 - 2 * (q1 * q1 + q3 * q3),
            2 * (q2 * q3 + q0 * q1),
        ], [
            2 * (q1 * q3 + q0 * q2),
            2 * (q2 * q3 - q0 * q1),
            1 - 2 * (q1 * q1 + q2 * q2),
        ]])

        return np.dot(m1, np.dot(m2, m3))

    def xy(self, ra, dec):
        """Convert ra/dec coordinates in map coordinates.

        Parameters
        ----------
        ra: float or array
            Right-ascension (degree).
        dec: float or array
            Declination (degree).

        Returns
        -------
        float or array, float or array
            X-Y map coordinates.

        """
        (cra, sra), (cdec, sdec) = self._cs(ra), self._cs(dec)

        if np.ndim(ra) == 0 and np.ndim(dec) == 0:
            shape = None
            xyz = np.dot(self.m, [cra * cdec, sra * cdec, sdec])
        else:
            if np.ndim(ra) > 0 and np.ndim(dec) == 0:
                shape = np.shape(ra)
            elif np.ndim(ra) == 0 and np.ndim(dec) > 0:
                shape = np.shape(dec)
            elif np.shape(ra) == np.shape(dec):
                shape = np.shape(ra)
            else:
                raise ValueError('RA and DEC arrays must have the same size.')

            xyz = np.zeros((3, np.prod(shape)))
            xyz[0] = (cra * cdec).ravel()
            xyz[1] = (sra * cdec).ravel()
            xyz[2] = sdec.ravel()

            np.dot(self.m, xyz, out=xyz)

        x, y = xyz[1] / xyz[0], xyz[2] / xyz[0]

        if shape is not None:
            x = np.reshape(x, shape)
            y = np.reshape(y, shape)

        return x, y

    def lonlat(self, x, y):
        """Alias for map coordinates in ra/dec coordinates.

        Parameters
        ----------
        x: float or array
            X-coordinate on the map [m].
        y: float or array
            Y-coordinate on the map [m].

        Returns
        -------
        float or array, float or array
            Right ascension and declination [degree].

        See also
        --------
        pyvims.projections.sky.Sky.radec

        """
        return self.radec(x, y)

    def radec(self, x, y):
        """Convert map coordinates in ra/dec coordinates.

        Parameters
        ----------
        x: float or array
            X-coordinate on the map [m].
        y: float or array
            Y-coordinate on the map [m].

        Returns
        -------
        float or array, float or array
            Right ascension and declination [degree].

        """
        if np.ndim(x) == 0 and np.ndim(y) == 0:
            shape = None
            u = [1, x, y]
        else:
            if np.ndim(x) > 0 and np.ndim(y) == 0:
                shape = np.shape(x)
            elif np.ndim(x) == 0 and np.ndim(y) > 0:
                shape = np.shape(y)
            elif np.shape(x) == np.shape(y):
                shape = np.shape(x)
            else:
                raise ValueError('X and Y arrays must have the same size.')

            u = np.ones((3, np.prod(shape)))
            u[1] = np.reshape(x, (-1))
            u[2] = np.reshape(y, (-1))

        norm = np.sqrt(np.sum(np.power(u, 2), axis=0))
        u = np.divide(u, norm)

        v = np.dot(self.m.T, u)
        ra = np.degrees(np.arctan2(v[1], v[0])) % 360
        dec = np.degrees(np.arcsin(v[2]))

        if shape is not None:
            ra = np.reshape(ra, shape)
            dec = np.reshape(dec, shape)

        return ra, dec
