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

    # Camera pixel size [rad/mm]
    PIXEL_SIZE = None

    # Camera focal length [m]
    FOCAL = None

    # Boresite location
    BORESITE = 31

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
            f'Pixel scale: {self.scale_l, self.scale_s}',
            f'Pixel size: {self.pixel_size_l, self.pixel_size_s}',
            f'Boresite: {self.boresite_l, self.boresite_s}',
            f'Offset: {self.offset_l, self.offset_s}',
        ])

    def _pixel_size(self, scale):
        """Scaled pixel size."""
        return self.PIXEL_SIZE / scale

    def _boresite(self, scale):
        """Scaled boresite.

        scale: 1 -> 31
        scale: 2 -> 62.5
        scale: 3 -> 94

        """
        return self.BORESITE * scale + (scale - 1) / 2

    @staticmethod
    def _offset(scale, offset, swath):
        """Scaled offset based on swath.

        scale: 1 -> offset - 1
        scale: 2 -> 2 * (offset - 1) + (swath - 1) / 2
        scale: 3 -> 3 * (offset + swath / 2) - swath / 2

        """
        return (scale * (offset - 1)
                + (scale - 1) * ((swath - 1) / 2 + (scale - 2) * 2))

    @property
    def scale_l(self):
        """Line scaling factor."""
        return self.SCALE[0]

    @property
    def scale_s(self):
        """Sample scaling factor."""
        return self.SCALE[1]

    @property
    def pixel_size_l(self):
        """Line scaled pixel size."""
        return self._pixel_size(self.scale_l)

    @property
    def pixel_size_s(self):
        """Sample scaled pixel size."""
        return self._pixel_size(self.scale_s)

    @property
    def boresite_l(self):
        """Line scaled boresight."""
        return self._boresite(self.scale_l)

    @property
    def boresite_s(self):
        """Sample scaled boresight."""
        return self._boresite(self.scale_s)

    @property
    def offset_l(self):
        """Line scaled offset."""
        return self._offset(self.scale_l, self.zoffset, self.swath_length)

    @property
    def offset_s(self):
        """Sample scaled offset."""
        return self._offset(self.scale_s, self.xoffset, self.swath_width)

    @property
    def grid(self):
        """Camera pixel grid (L, S)."""
        if self.__grid is None:
            l = np.arange(1, self.swath_length + 1)
            s = np.arange(1, self.swath_width + 1)

            self.__grid = np.meshgrid(l, s, indexing='ij')

        return self.__grid


class VIMSCameraVis(VIMSCameraAbstract):
    """VIMS-VIS camera in ``NORMAL`` sampling mode."""

    PIXEL_SIZE = 0.506e-3
    FOCAL = 143.0e-3


class VIMSCameraIr(VIMSCameraAbstract):
    """VIMS-IR camera in ``NORMAL`` sampling mode."""

    PIXEL_SIZE = 0.495e-3
    FOCAL = 426.0e-3


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
