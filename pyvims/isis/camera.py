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

    # Boresite location (X, Y)
    BORESITE = np.array([[[32]], [[32]]])

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
            f'Swath: {self.swath}',
            f'Offset: {self.offset}',
            f'Scaling: {self.scale}',
            f'Pixel size: {self.PIXEL_SIZE * 1e3} mrad/pix',
            f'Boresite: {tuple(self.BORESITE.flatten())}',
        ])

    @property
    def swath(self):
        """Camera swath (x, y)."""
        return self.swath_x, self.swath_y

    @property
    def offset(self):
        """Camera offset (x, y)."""
        return self.offset_x, self.offset_y

    @property
    def scale_x(self):
        """Scaling factor in X direction."""
        return self.SCALE[0]

    @property
    def scale_y(self):
        """Scaling factor in Y direction."""
        return self.SCALE[1]

    @property
    def scale(self):
        """Camera scale (x, y)."""
        return self.scale_x, self.scale_y

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
    def cgrid(self):
        """Camera grid FOV contour.

        Note
        ----
        The corners pixels are set on circle or an ellipse
        based on the shape of the pixel (:py:attr:`scale`).

        """
        x, y = self._x, self._y
        xl, xr, yt, yb = x[0], x[-1], y[0], y[-1]

        a, b = .5 / np.array(self.scale)
        xc, yc = a / np.sqrt(2), b / np.sqrt(2)

        return np.hstack([
            [[xl - xc], [yt - yc]],              # Top-Left corner
            [x, self.swath_x * [yt - b]],        # Top edge
            [[xr + xc], [yt - yc]],              # Top-Right corner
            [self.swath_y * [xr + a], y],        # Right edge
            [[xr + xc], [yb + yc]],              # Bottom-Right corner
            [x[::-1], self.swath_x * [yb + b]],  # Bottom edge
            [[xl - xc], [yb + yc]],              # Bottom-Left corner
            [self.swath_y * [xl - a], y[::-1]],  # Left edge
            [[xl - xc], [yt - yc]],              # Top-Left corner
        ])

    @property
    def corner_grid(self):
        """Camera grid pixel corners.

        Note
        ----
        Corner are defined as diagonal points
        compare to the pixel center.

        """
        x, y = self._x, self._y

        a, b = .5 / np.array(self.scale)

        tl = np.meshgrid(x - a, y + b)
        tr = np.meshgrid(x + a, y + b)
        bl = np.meshgrid(x - a, y - b)
        br = np.meshgrid(x + a, y - b)

        return np.moveaxis([tl, tr, bl, br], 0, 3)

    @property
    def edge_grid(self):
        """Camera grid pixel edges."""
        x, y = self._x, self._y

        a, b = .5 / np.array(self.scale)

        l = np.meshgrid(x - a, y)
        r = np.meshgrid(x + a, y)
        t = np.meshgrid(x, y + b)
        b = np.meshgrid(x, y - b)

        return np.moveaxis([l, r, t, b], 0, 3)

    @property
    def fgrid(self):
        """Camera grid pixel footprint.

        Note
        ----
        The corners pixels are set on circle or an ellipse
        based on the shape of the pixel (:py:attr:`scale`).

        """
        x, y = self._x, self._y

        a, b = .5 / np.array(self.scale) / np.sqrt(2)

        tl = np.meshgrid(x - a, y + b)
        tr = np.meshgrid(x + a, y + b)
        bl = np.meshgrid(x - a, y - b)
        br = np.meshgrid(x + a, y - b)

        l, r, t, b = np.moveaxis(self.edge_grid, 3, 0)

        return np.moveaxis([tl, t, tr, r, br, b, bl, l, tl], 0, 3)

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
        shape = (3, *np.shape(x))
        if np.ndim(x) == 1:
            x, y = [x], [y]
        elif np.ndim(x) == 3:
            s = (2, 1, np.size(x) // 2)
            x, y = np.reshape(x, s), np.reshape(y, s)

        phi, theta = (np.array([x, y]) - self.BORESITE) * self.PIXEL_SIZE
        return np.reshape([
            np.cos(theta) * np.sin(phi),
            np.sin(theta),
            np.cos(theta) * np.cos(phi),
        ], shape)

    @property
    def pixels(self):
        """Camera pixels orientation in J2000 frame.

        Return
        ------
        array(3, NL, NS)
            Pixel boresights in Camera frame.
        """
        if self.__pixels is None:
            self.__pixels = self.xy2ang(*self.grid)
        return self.__pixels

    @property
    def cpixels(self):
        """Camera contour pixels orientation in J2000 frame.

        Return
        ------
        array(3, N)
            Pixel contours boresights in Camera frame.
        """
        return self.xy2ang(*self.cgrid)

    @property
    def corner_pixels(self):
        """Camera corner pixels orientation in J2000 frame.

        Return
        ------
        array(3, NL, NS, 4)
            Pixel corners boresights in Camera frame.

        Note
        ----
        Corner are defined as diagonal points
        compare to the pixel center.

        """
        return self.xy2ang(*self.corner_grid)

    @property
    def edge_pixels(self):
        """Camera edge pixels orientation in J2000 frame.

        Return
        ------
        array(3, NL, NS, 4)
            Pixel edges boresights in Camera frame.

        """
        return self.xy2ang(*self.edge_grid)

    @property
    def fpixels(self):
        """Camera footprint pixels orientation in J2000 frame.

        Return
        ------
        array(3, NL, NS, 9)
            Pixel footprints boresights in Camera frame.

        """
        return self.xy2ang(*self.fgrid)

    @property
    def pix_res_x(self):
        """Pixel angular resolution in X direction."""
        return 2 * np.tan(self.PIXEL_SIZE / (2 * self.scale_x))

    @property
    def pix_res_y(self):
        """Pixel angular resolution in Y direction."""
        return 2 * np.tan(self.PIXEL_SIZE / (2 * self.scale_y))

    @property
    def pix_res(self):
        """Mean pixel angular resolution."""
        return np.sqrt(self.pix_res_x * self.pix_res_y)


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
