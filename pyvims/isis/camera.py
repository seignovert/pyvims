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

    # Boresite location (33rd pixels from top left corner)
    BORESITE = 32

    # Camera pixel size [rad/pixel]
    PIXEL_SIZE = None

    # Pixel scaling factor in (L, S) direction
    SCALE = (1, 1)

    def __init__(self, offsets, swaths):
        self.xoffset, self.zoffset = offsets
        self.swath_width, self.swath_length = swaths

        self.__grid = None
    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return '\n - '.join([
            f'<{self}>',
            f'Swath: {self.swath_width, self.swath_length}',
            f'Offset: {self.xoffset, self.zoffset}',
            f'Pixel scale: {self.scale_s, self.scale_l}',
            f'Pixel size: {self.PIXEL_SIZE}',
            f'Focal length: {self.PIXEL_SIZE}',
            f'Boresite: {self.BORESITE, self.BORESITE}',
        ])

    @property
    def scale_l(self):
        """Line scaling factor."""
        return self.SCALE[0]

    @property
    def scale_s(self):
        """Sample scaling factor."""
        return self.SCALE[1]

    @staticmethod
    def _positions(offset, swath, scale):
        """Scaled initial pixel position."""
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
    def _l(self):
        """Line position on the sensor."""
        return self._positions(self.zoffset, self.swath_length, self.scale_l)

    @property
    def _s(self):
        """Scaled sample position on the sensor."""
        return self._positions(self.xoffset, self.swath_width, self.scale_s)

    @property
    def grid(self):
        """Camera pixel grid (L, S)."""
        if self.__grid is None:
            self.__grid = np.meshgrid(self._l, self._s, indexing='ij')
        return self.__grid

    @property
    def extent(self):
        """Camera grid extent."""
        return [self._s[0] - .5 / self.scale_s,
                self._s[-1] + .5 / self.scale_s,
                self._l[-1] + .5 / self.scale_l,
                self._l[0] - .5 / self.scale_l]


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

    SCALE = (1, 2)


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
