"""VIMS plot module."""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from .errors import VIMSError
from .projections import ortho_cube, sky_cube


def plot_cube(c, *args, **kwargs):
    """Generic cube plot."""
    if not args:
        raise VIMSError('Not attribute provided: '
                        'band(s), wavelength(s), (S, L) coordinates or keyword')

    if len(args) > 1:
        if 'bands' in args:
            kwargs['as_bands'] = True

    if isinstance(args[0], (int, float, str)):
        if 'sky' in args:
            return plot_sky(c, args[0], **kwargs)

        if 'ortho' in args:
            return plot_ortho(c, args[0], **kwargs)

        return plot_img(c, args[0], **kwargs)

    if isinstance(args[0], tuple):
        if len(args[0]) == 2:
            return plot_spectrum(c, *args[0], **kwargs)

        if len(args[0]) == 3:
            if 'sky' in args:
                return plot_sky(c, args[0], **kwargs)

            if 'ortho' in args:
                return plot_ortho(c, args[0], **kwargs)

            return plot_img(c, args[0], **kwargs)

    if isinstance(args[0], list):
        if isinstance(args[0][0], tuple):
            return plot_spectra(c, *args[0], **kwargs)


def plot_img(c, index, ax=None, title=None,
             ticks=True, labels=True, figsize=(8, 8),
             cmap='gray', interp='bicubic', ir_hr=False,
             **kwargs):
    """Plot VIMS cube image.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to plot.
    index: int or float
        VIMS band or wavelength to plot.
    ax: matplotlib.axis, optional
        Optional matplotlib axis object.
    title: str, optional
        Figure title.
    ticks: bool, optional
        Show sample and line ticks.
    labels: bool, optional
        Show sample and line labels.
    figsize: tuple, optional
        Pyplot figure size.
    cmap: str, optional
        Pyplot colormap keyword.
    interp: str, optional
        Interpolation choice (see :py:func:`pyplot.imshow` for details).
    ir_hr: bool, optional
        Infrared high resolution aspect ratio (before projection).

    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    ax.imshow(c[index], cmap=cmap, extent=c.extent, interpolation=interp)

    if title is None:
        if isinstance(index, int):
            title = f'{c} on band {index}'
        elif isinstance(index, float):
            title = f'{c} at {index:.2f} µm'
        elif isinstance(index, str):
            title = f'{c} with `{index}`'
        elif isinstance(index, tuple):
            if isinstance(index[0], float):
                title = f'{c} at ({index[0]:.2f}, {index[1]:.2f}, {index[2]:.2f}) µm'
            else:
                title = f'{c} on bands {index}'

    if ir_hr:
        ax.set_aspect(2)

    if title:
        ax.set_title(title)

    if ticks:
        ax.set_xticks(c.sticks)
        ax.set_yticks(c.lticks)

    if labels:
        ax.set_xlabel(c.slabel)
        ax.set_ylabel(c.llabel)

    return ax


def plot_spectrum(c, S, L, offset=0, color=None, as_bands=False, ax=None,
                  title=None, ticks=True, labels=True, label=None,
                  figsize=(12, 6), **kwargs):
    """Plot VIMS cube spectrum.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to plot.
    S: int
        Spectrum sample location (``1`` to ``NS``).
    L: int
        Spectrum line location (``1`` to ``NL``).
    offset: float, optional
        Spectrum offset.
    color: str, optional
        Spectrum line color.
    as_bands: bool, optional
        Display as bands on X-axis.
    ax: matplotlib.axis, optional
        Optional matplotlib axis object.
    title: str, optional
        Figure title.
    ticks: bool, optional
        Show wavelengths/bands and I/F ticks.
    labels: bool, optional
        Show wavelengths/bands and I/F labels.
    labels: str, optional
        Spectrum label.
    figsize: tuple, optional
        Pyplot figure size.

    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    if as_bands:
        x = c.bands
        xticks = c.bticks
        xlabel = c.blabel
    else:
        x = c.wvlns
        xticks = c.wticks
        xlabel = c.wlabel

    if label is None:
        label = f'S={S}, L={L}'

    ax.plot(x, c[S, L] + offset, label=label, color=color)

    if title is None:
        title = f'{c} at S={S}, L={L}'

    if title:
        ax.set_title(title)

    if ticks:
        ax.set_xticks(xticks)

    if labels:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(c.ilabel)

    return ax


def _extract(n, key, kwargs, default=None):
    """Extract key from kwargs and set repetition if needed.

    Parameters
    ----------
    n: int
        Number of repetition.
    key: str
        Input key.
    kwargs: dict
        Arguments key-values dictionary.
    default: any
        Default value.

    """
    if key in kwargs.keys():
        values = kwargs[key]
        del kwargs[key]

        if isinstance(values, (int, float)):
            values = np.arange(0, n * values, values)

        elif isinstance(values, str):
            values = n * [values]

        elif isinstance(values, (list, tuple)):
            if len(values) != n:
                raise VIMSError('`coordinates` and `offset` must have '
                                f'the same length ({n} vs. {len(values)}).')
        else:
            raise VIMSError
    else:
        values = n * [default]

    return values


def plot_spectra(c, *coordinates, legend=True, **kwargs):
    """Plot multiple specra on the same plot.

    Parameters
    ----------
    coordinates: [(int, int), …]
        Sprectrum coordinates.
    legend: bool, optional
        Show spectra legend.

    """
    n = len(coordinates)
    offsets = _extract(n, 'offset', kwargs, default=0)
    colors = _extract(n, 'color', kwargs)
    labels = _extract(n, 'label', kwargs)

    ax = None
    for (S, L), offset, color, label in zip(coordinates, offsets, colors, labels):
        ax = plot_spectrum(c, S, L, offset=offset, color=color, label=label,
                           title=False, ax=ax, **kwargs)

    if 'title' not in kwargs.keys():
        title = f'{c}'

    if title:
        ax.set_title(title)

    if legend:
        ax.legend()


def plot_sky(c, index, ax=None, title=None,
             labels=True,
             figsize=(8, 8), cmap='gray',
             twist=0, n_interp=512,
             interp='cubic', grid='lightgray',
             show_img=True, show_pixels=False,
             show_contour=False, **kwargs):
    """Plot projected VIMS cube image on the sky.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to plot.
    index: int or float
        VIMS band or wavelength to plot.
    ax: matplotlib.axis, optional
        Optional matplotlib axis object.
    title: str, optional
        Figure title.
    ticks: bool, optional
        Show sample and line ticks.
    labels: bool, optional
        Show sample and line labels.
    figsize: tuple, optional
        Pyplot figure size.
    cmap: str, optional
        Pyplot colormap keyword.
    twist: float, optional
        Camera poiting twist angle (degree).
    n: int, optional
        Number of pixel for the grid interpolation.
    interp: str, optional
        Interpolation method (see :py:func:`scipy.griddata` for details).
    grid: str, optional
        Color grid. Set ``None`` to remove the grid.

    """
    def _ticks_levels(cnt, x, p_x):
        """Extract levels from contour.

        Parameters
        ----------
        cnt: pyplot.contour
            Pyplot contour
        x: np.array
            Input values.
        p_x: np.array
            Projected values on the grid.

        Returns
        -------
        list
            Visible contour levels.

        """
        levels = cnt.levels
        labels = _ticks_fmt(levels)
        ticks = np.interp(levels, x, p_x)
        valid = (ticks != p_x[0]) & (ticks != p_x[-1])
        return ticks[valid], labels[valid]

    def _ticks_fmt(t, suffix='°'):
        """Format ticks labels.

        Parameters
        ----------
        t: list
            Ticks values.
        suffix: str, optional
            Add suffix to tick labels.

        Returns
        -------
        [str. …]
            Ticks labels.

        """
        d = max(-int(np.log10(t[-1] - t[0]) - 1.5), 0)
        return np.array(['{v:0.{d}f}{s}'.format(v=v, d=d, s=suffix) for v in t])

    img, (x, y), extent, pix, cnt, (ra, dec) = sky_cube(c, index,
                                                        twist=twist,
                                                        n=n_interp,
                                                        interp=interp)

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    if show_img:
        ax.imshow(img, cmap=cmap, extent=extent)

    if show_pixels:
        ax.scatter(*pix, s=25, facecolors='none', edgecolors=show_pixels)

    if show_contour:
        ax.plot(*cnt, '-', color=show_contour)

    if title is None:
        if isinstance(index, int):
            title = f'{c} on band {index}'
        elif isinstance(index, float):
            title = f'{c} at {index:.2f} µm'
        elif isinstance(index, str):
            title = f'{c} | {index.title()}'
        elif isinstance(index, tuple):
            if isinstance(index[0], float):
                title = f'{c} at ({index[0]:.2f}, {index[1]:.2f}, {index[2]:.2f}) µm'
            else:
                title = f'{c} on bands {index}'

    if grid is not None:
        cextent = [extent[0], extent[1], extent[3], extent[2]]
        cx = ax.contour(ra, extent=cextent, colors=grid, linewidths=.75)
        cy = ax.contour(dec, extent=cextent, colors=grid, linewidths=.75)

        tx, lx = _ticks_levels(cx, ra[0, :], x[0, :])
        ty, ly = _ticks_levels(cy, dec[:, -1], y[:, -1])

        ax.set_xticks(tx)
        ax.set_yticks(ty)
        ax.set_xticklabels(lx)
        ax.set_yticklabels(ly)

        ax.set_xlim(extent[:2])
        ax.set_ylim(extent[2:])

    if title:
        ax.set_title(title)

    if labels:
        ax.set_xlabel('Right ascension')
        ax.set_ylabel('Declination')

    # Reverse Ra-Dec axis
    ax.invert_xaxis()
    ax.invert_yaxis()
    return ax


def plot_ortho(c, index, ax=None, title=None,
               labels=True,
               figsize=(8, 8), cmap='gray',
               twist=0, n_interp=512,
               interp='cubic', grid='lightgray',
               show_img=True, show_pixels=False,
               show_contour=False, **kwargs):
    """Plot projected VIMS cube image in median orthographic plane.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to plot.
    index: int or float
        VIMS band or wavelength to plot.
    ax: matplotlib.axis, optional
        Optional matplotlib axis object.
    title: str, optional
        Figure title.
    ticks: bool, optional
        Show sample and line ticks.
    labels: bool, optional
        Show sample and line labels.
    figsize: tuple, optional
        Pyplot figure size.
    cmap: str, optional
        Pyplot colormap keyword.
    twist: float, optional
        Camera poiting twist angle (degree).
    n: int, optional
        Number of pixel for the grid interpolation.
    interp: str, optional
        Interpolation method (see :py:func:`scipy.griddata` for details).
    grid: str, optional
        Color grid. Set ``None`` to remove the grid.

    """
    img, (x, y), extent, pix, cnt, (lon, lat, alt) = ortho_cube(c, index,
                                                                n=n_interp,
                                                                interp=interp)

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    if show_img:
        ax.imshow(img, cmap=cmap, extent=extent)

    if show_pixels:
        ax.scatter(*pix, s=25, facecolors='none', edgecolors=show_pixels)

    if show_contour:
        ax.plot(*cnt, '-', color=show_contour)

    if title is None:
        if isinstance(index, int):
            title = f'{c} on band {index}'
        elif isinstance(index, float):
            title = f'{c} at {index:.2f} µm'
        elif isinstance(index, str):
            title = f'{c} | {index.title()}'
        elif isinstance(index, tuple):
            if isinstance(index[0], float):
                title = f'{c} at ({index[0]:.2f}, {index[1]:.2f}, {index[2]:.2f}) µm'
            else:
                title = f'{c} on bands {index}'

    if grid is not None:
        cextent = [extent[0], extent[1], extent[3], extent[2]]

        is_limb = alt > 1e-6

        glon = np.ma.array(lon, mask=is_limb)
        glat = np.ma.array(lat, mask=is_limb)

        _lon_offset = c.sc_lon

        clon = (glon - _lon_offset + 180) % 360 - 180
        clat = lat

        dlon = np.max(clon) - np.min(clon)
        dlat = np.max(clat) - np.min(clat)

        if dlon > 90:
            lons = np.arange(-180, 360, 30) - _lon_offset
        elif dlon > 30:
            lons = np.arange(-180, 360, 10) - _lon_offset
        else:
            lons = np.arange(int(np.min(clon)), int(np.max(clon)), 1)

        if dlat > 90:
            lats = np.arange(-90, 90, 30)
        elif dlat > 30:
            lats = np.arange(-90, 90, 10)
        else:
            lats = np.arange(int(np.min(clat)), int(np.max(clat)), 1)

        alts = np.arange(500, np.max(alt), 500)

        @FuncFormatter
        def _fmt_lon(x, pos=None):
            lon = (x + _lon_offset + 180) % 360 - 180
            s = '' if lon == 0 else ('W' if lon > 0 else 'E')
            return f'{abs(lon):.0f}°{s}'

        @FuncFormatter
        def _fmt_lat(x, pos=None):
            s = '' if x == 0 else ('N' if x > 0 else 'S')
            return f'{abs(x):.0f}°{s}'

        @FuncFormatter
        def _fmt_alt(x, pos=None):
            return f'{x:.0f} km'

        kwargs = {
            'extent': cextent,
            'colors': grid,
            'linewidths': .75,
            'linestyles': 'solid'
        }

        llon = ax.contour(clon, lons, **kwargs)
        llat = ax.contour(clat, lats, **kwargs)

        lalt = ax.contour(alt, alts, **kwargs)
        ax.contour(alt, [0], **kwargs)

        ax.clabel(llon, fmt=_fmt_lon, inline=True, use_clabeltext=True)
        ax.clabel(llat, fmt=_fmt_lat, inline=True, use_clabeltext=True)
        ax.clabel(lalt, fmt=_fmt_alt, inline=True, use_clabeltext=True)

        # Polar reticule for large FOV
        r = c.target_radius
        kwargs_r = {'color': kwargs['colors'], 'linewidth': kwargs['linewidths']}
        ax.plot([0, 0], [extent[2], r], '-', **kwargs_r)
        ax.plot([0, 0], [-r, extent[3]], '-', **kwargs_r)

        ax.set_xticks([])
        ax.set_yticks([])

        ax.set_xlim(extent[:2])
        ax.set_ylim(extent[2:])

    if title:
        ax.set_title(title)

    if labels:
        ax.set_xlabel('← West / East →')
        ax.set_ylabel('← South / North →')

    ax.invert_yaxis()
    return ax
