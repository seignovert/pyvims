"""VIMS camera model."""

import numpy as np

from .errors import VIMSCameraError


class VIMSCameraAbstract:
    """Abstract VIMS Camera object.

    Parameters
    ----------
    offsets: [int, int]
        Acquisition X and Z offsets.
    swaths: [int, int]
        Acquisition width and length swaths.

    """

    # Boresite location
    BORESITE = 33

    # Camera pixel size [rad/pixel]
    PIXEL_SIZE = None

    # Pixel scaling factor in (X, Y) direction
    SCALE = (1, 1)

    def __init__(self, offsets, swaths):
        self.offset_x, self.offset_y = offsets
        self.swath_x, self.swath_y = swaths

        self.__grid = None
        self.__pixels = None

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return '\n - '.join([
            f'<{self}>',
            f'Swath: {self.swath_x, self.swath_y}',
            f'Offset: {self.offset_x, self.offset_y}',
            f'Scaling: {self.scale_x, self.scale_y}',
            f'Pixel size: {self.PIXEL_SIZE * 1e3} mrad/pix',
            f'Boresite: {self.BORESITE, self.BORESITE}',
        ])

    @property
    def scale_x(self):
        """Scaling factor in X direction."""
        return self.SCALE[0]

    @property
    def scale_y(self):
        """Scaling factor in Y direction."""
        return self.SCALE[1]

    @staticmethod
    def _positions(offset, swath, scale):
        """Scaled initial pixel position (X, Y).

        Pixel position are expressed in the
        camera focal plane.

        """
        if scale == 1:
            start = offset
        elif scale == 2:
            start = offset + (swath//2)/2 - 1/4
        elif scale == 3:
            start = offset + swath/3 - 1/3
        else:
            raise VIMSCameraError(f'Scale value must be 1, 2, or 3.')

        stop = start + (swath - 1) / scale
        return np.linspace(start, stop, swath)

    @property
    def _x(self):
        """Scaled sample position on the sensor."""
        return self._positions(self.offset_x, self.swath_x, self.scale_x)

    @property
    def _y(self):
        """Line position on the sensor."""
        return self._positions(self.offset_y, self.swath_y, self.scale_y)

    @property
    def grid(self):
        """Camera pixel grid (X, Y)."""
        if self.__grid is None:
            self.__grid = np.asarray(np.meshgrid(self._x, self._y))
            self.__pixels = None
        return self.__grid

    @property
    def extent(self):
        """Camera grid extent."""
        return [self._x[0] - .5 / self.scale_x,
                self._x[-1] + .5 / self.scale_x,
                self._y[-1] + .5 / self.scale_y,
                self._y[0] - .5 / self.scale_y]

    def xy2ang(self, x, y):
        """Convert pixel coordinates in camera look vector.

        Parameters
        ----------
        x: float or np.array
            Sample coordinates on the sensor.
        y: float or np.array
            Line coordinates on the sensor.

        Return
        ------
        (float, float, float)
            XYZ normalized pixel vector in Camera frame.

        """
        phi, theta = (np.array([x, y]) - self.BORESITE) * self.PIXEL_SIZE
        return np.array([
            np.cos(theta) * np.sin(phi),
            np.sin(theta),
            np.cos(theta) * np.cos(phi),
        ])

    @property
    def pixels(self):
        """Camera pixels orientation in J2000 frame.

        Return
        ------
        array(3, NS, NL)
            Pixel boresights in Camera frame.
        """
        if self.__pixels is None:
            self.__pixels = self.xy2ang(*self.grid)
        return self.__pixels


class VIMSCameraVis(VIMSCameraAbstract):
    """VIMS-VIS camera in ``NORMAL`` sampling mode."""

    PIXEL_SIZE = 0.506e-3


class VIMSCameraIr(VIMSCameraAbstract):
    """VIMS-IR camera in ``NORMAL`` sampling mode."""

    PIXEL_SIZE = 0.495e-3


class VIMSCameraVisHR(VIMSCameraVis):
    """VIMS-VIS camera in ``HI-RES`` sampling mode."""

    SCALE = (3, 3)


class VIMSCameraIrHR(VIMSCameraIr):
    """VIMS-IR camera in ``HI-RES`` sampling mode."""

    SCALE = (2, 1)


class VIMSCamera:
    """VIMS Camera object.

    Parameters
    ----------
    channel: str
        Camera channel (``VIS``|``IR``).
    mode: str
        Acquisition sampling mode (``NORMAL``|``HI-RES``).
    offsets: [int, int]
        Acquisition X and Z offsets.
    swaths: [int, int]
        Acquisition width and length swaths.

    """

    def __new__(cls, channel, mode, offsets, swaths):

        if channel not in ['VIS', 'IR']:
            raise VIMSCameraError(f'Unknown channel `{channel}`. '
                                  'Only `VIS` and `IR` are available')

        if mode not in ['NORMAL', 'HI-RES']:
            raise VIMSCameraError(f'Unknown sampling mode `{mode}`. '
                                  'Only `NORMAL` and `HI-RES` are available')

        if mode == 'NORMAL' and channel == 'IR':
            return VIMSCameraIr(offsets, swaths)

        if mode == 'NORMAL' and channel == 'VIS':
            return VIMSCameraVis(offsets, swaths)

        if mode == 'HI-RES' and channel == 'IR':
            return VIMSCameraIrHR(offsets, swaths)

        if mode == 'HI-RES' and channel == 'VIS':
            return VIMSCameraVisHR(offsets, swaths)

        return None
