"""VIMS plot module."""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from .errors import VIMSError
from .projections import equi_cube, ortho_cube, polar_cube, sky_cube
from .vectors import deg180, deg360


@FuncFormatter
def _fmt_lon(x, pos=None):
    s = '' if x in [0, 180, -180] else ('W' if x > 0 else 'E')
    return f'{abs(x):.0f}°{s}'


@FuncFormatter
def _fmt_lon_180(x, pos=None):
    return _fmt_lon(deg180(x), pos=pos)


@FuncFormatter
def _fmt_lat(x, pos=None):
    s = '' if x == 0 else ('N' if x > 0 else 'S')
    return f'{abs(x):.0f}°{s}'


@FuncFormatter
def _fmt_alt(x, pos=None):
    return f'{x:.0f} km'


def _title(c, index):
    """Generic image title if not provided.

    Parameters
    -----------
    c: pyvims.VIMS
        Cube to plot.
    index: int, float, str or tuple
        VIMS band or wavelength to plot.

    Returns
    -------
    str
        Default title.

    """
    if isinstance(index, int):
        return f'{c} on band {index}'

    if isinstance(index, float):
        return f'{c} at {index:.2f} µm'

    if isinstance(index, str):
        if 'um' in index:
            return f'{c} | {index.replace("um", " µm")}'
        return f'{c} | {index.title()}'

    if isinstance(index, tuple):
        if isinstance(index[0], float):
            return f'{c} at ({index[0]:.2f}, {index[1]:.2f}, {index[2]:.2f}) µm'

        else:
            return f'{c} on bands {index}'

    return None


def _circle(r, npt=181):
    """Circle coordinates."""
    theta = np.linspace(0, 2 * np.pi, npt)
    ct, st = np.cos(theta), np.sin(theta)
    return [r * ct, r * st]


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

        if 'equi' in args:
            return plot_equi(c, args[0], **kwargs)

        if 'polar' in args:
            return plot_polar(c, args[0], **kwargs)

        if 'all' in args:
            return plot_all(c, args[0], **kwargs)

        if 'specular' == args[0]:
            return plot_spectra(c, *c.specular_sl, **kwargs)

        if 'specular' in args:
            return plot_specular(c, args[0], **kwargs)

        return plot_img(c, args[0], **kwargs)

    if isinstance(args[0], tuple):
        if len(args[0]) == 2:
            return plot_spectrum(c, *args[0], **kwargs)

        if len(args[0]) == 3:
            if 'sky' in args:
                return plot_sky(c, args[0], **kwargs)

            if 'ortho' in args:
                return plot_ortho(c, args[0], **kwargs)

            if 'equi' in args:
                return plot_equi(c, args[0], **kwargs)

            if 'polar' in args:
                return plot_polar(c, args[0], **kwargs)

            if 'all' in args:
                return plot_all(c, args[0], **kwargs)

            return plot_img(c, args[0], **kwargs)

    if isinstance(args[0], list):
        if isinstance(args[0][0], tuple):
            return plot_spectra(c, *args[0], **kwargs)


def plot_img(c, index, ax=None, title=None,
             ticks=True, labels=True, figsize=(8, 8),
             cmap='gray', interp='none', ir_hr=False,
             show_specular=False, show_legend=None,
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
    show_specular: bool, optional
        Show specular pixel location.
    show_legend: bool, optional
        Show specular pixel legend.

    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    ax.imshow(c[index], cmap=cmap, extent=c.extent, interpolation=interp)

    if show_specular:
        edgecolors = 'r' if not isinstance(show_specular, str) else show_specular
        ax.scatter(*c.specular_sl.T, facecolors='none', edgecolors=edgecolors,
                   label=f'Specular: {c.specular_sl}')
        show_legend = True if show_legend is None else show_legend

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

    if show_legend:
        ax.legend()

    ax.set_xlim(.5, c.NS + .5)
    ax.set_ylim(c.NL + .5, .5)

    return ax


def plot_spectrum(c, S, L, offset=0, color=None, as_bands=False,
                  as_sigma=False, ax=None,
                  title=None, ticks=True, labels=True, label=None,
                  hot_pixels=False,
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
    as_sigma: bool, optional
        Display as wavenumbers on X-axis.
    ax: matplotlib.axis, optional
        Optional matplotlib axis object.
    title: str, optional
        Figure title.
    ticks: bool, optional
        Show wavelengths/bands and I/F ticks.
    labels: bool, optional
        Show wavelengths/bands and I/F labels.
    label: str, optional
        Spectrum label.
    hot_pixels: bool, optional
        Show hot pixels (default: False).
    figsize: tuple, optional
        Pyplot figure size.

    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    if as_bands:
        x = c.bands
        xticks = c.bticks
        xlabel = c.blabel
        xhotpix = c.hot_pixels()
    elif as_sigma:
        x = c.sigma
        xticks = c.nticks
        xlabel = c.nlabel
        xhotpix = 1e4 / c.w_hot_pixels()
    else:
        x = c.wvlns
        xticks = c.wticks
        xlabel = c.wlabel
        xhotpix = c.w_hot_pixels()

    if label is None:
        label = f'S={S}, L={L}'

    ax.plot(x, c[S, L].spectrum + offset, label=label, color=color)

    if hot_pixels:
        [ax.axvline(x, ls='--', lw=.5, color='r') for x in xhotpix]

    if title is None:
        title = f'{c} at S={S}, L={L}'

    if title:
        ax.set_title(title)

    if ticks:
        ax.set_xticks(xticks)

    if labels:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(c.ilabel)

    if as_sigma:
        ax.set_xlim(4250, 1900)

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

        if n == 0:
            return values

        if isinstance(values, bool):
            values = [values] + (n - 1) * [default]

        if isinstance(values, (int, float)):
            values = np.arange(0, n * values, values)

        elif isinstance(values, str):
            values = n * [values]

        elif isinstance(values, (list, tuple)):
            if len(values) != n:
                raise VIMSError('`coordinates` and `offset` must have '
                                f'the same length ({n} vs. {len(values)}).')

        else:
            raise TypeError(
                f'Unknown key `{key}` value type `{type(values)}` to extract.')
    else:
        values = n * [default] if n > 0 else default

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
    ax = _extract(0, 'ax', kwargs, default=None)
    title = _extract(0, 'title', kwargs, default=f'{c}')
    hotpixs = _extract(n, 'hot_pixels', kwargs, default=False)

    for (S, L), offset, color, label, hotpix in zip(
            coordinates, offsets, colors, labels, hotpixs):
        ax = plot_spectrum(c, S, L, offset=offset, color=color, label=label,
                           hot_pixels=hotpix, title=title, ax=ax, **kwargs)

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
        opts = {}
        if 'alpha' in kwargs:
            opts['alpha'] = kwargs['alpha']
        if 'vmin' in kwargs:
            opts['vmin'] = kwargs['vmin']
        if 'vmax' in kwargs:
            opts['vmax'] = kwargs['vmax']

        ax.imshow(img, cmap=cmap, extent=extent, **opts)

    if show_pixels:
        ax.scatter(*pix, s=25, facecolors='none', edgecolors=show_pixels)

    if show_contour:
        ax.plot(*cnt, '-', color=show_contour)

    if title is None:
        title = _title(c, index)

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
        opts = {}
        if 'alpha' in kwargs:
            opts['alpha'] = kwargs['alpha']
        if 'vmin' in kwargs:
            opts['vmin'] = kwargs['vmin']
        if 'vmax' in kwargs:
            opts['vmax'] = kwargs['vmax']

        ax.imshow(img, cmap=cmap, extent=extent, **opts)

    if show_pixels:
        ax.scatter(*pix, s=25, facecolors='none', edgecolors=show_pixels)

    if show_contour:
        ax.plot(*cnt, '-', color=show_contour)

    if title is None:
        title = _title(c, index)

    if grid is not None:
        cextent = [extent[0], extent[1], extent[3], extent[2]]

        is_limb = alt > 1e-6

        glon = np.ma.array(lon, mask=is_limb)
        # glat = np.ma.array(lat, mask=is_limb)

        clon = np.ma.array(glon, mask=(np.abs(glon) > 95))
        clon_180 = np.ma.array(deg360(glon), mask=(np.abs(glon) < 95))
        clat = lat

        kwargs = {
            'extent': cextent,
            'colors': grid,
            'linewidths': .75,
            'linestyles': 'solid'
        }

        dlon = np.max(clon) - np.min(clon)
        dlat = np.max(clat) - np.min(clat)

        # Longitude grid
        if dlon > 90:
            lons = np.arange(-90, 90 + 30, 30)
            lons_180 = np.arange(90, 270 + 30, 30)
        elif dlon > 30:
            lons = np.arange(-90, 90 + 10, 10)
            lons_180 = np.arange(90, 270 + 10, 10)
        else:
            clon = glon
            lons = np.arange(int(np.min(clon)), int(np.max(clon)))

        llon = ax.contour(clon, lons, **kwargs)
        ax.clabel(llon, fmt=_fmt_lon, inline=True, use_clabeltext=True)

        if dlon > 30:
            llon_180 = ax.contour(clon_180, lons_180, **kwargs)
            ax.clabel(llon_180, fmt=_fmt_lon_180, inline=True, use_clabeltext=True)

        # Latitude grid
        if dlat > 90:
            lats = np.arange(-90, 90, 30)
        elif dlat > 30:
            lats = np.arange(-90, 90, 10)
        else:
            lats = np.arange(int(np.min(clat)), int(np.max(clat)))

        llat = ax.contour(clat, lats, **kwargs)
        ax.clabel(llat, fmt=_fmt_lat, inline=True, use_clabeltext=True)

        # Altitude grid
        alts = np.arange(500, np.max(alt), 500)
        lalt = ax.contour(alt, alts, **kwargs)
        ax.clabel(lalt, fmt=_fmt_alt, inline=True, use_clabeltext=True)

        # Planet cercle
        ax.contour(alt, [.1], **kwargs)

        # Polar reticule for large FOV
        r = c.target_radius
        kwargs_r = {'color': kwargs['colors'], 'linewidth': kwargs['linewidths']}
        ax.plot([0, 0], [extent[2], r], '-', **kwargs_r)
        ax.plot([0, 0], [-r, extent[3]], '-', **kwargs_r)

        # Remove old ticks
        ax.set_xticks([])
        ax.set_yticks([])

        # Scale limits to extent
        ax.set_xlim(extent[:2])
        ax.set_ylim(extent[2:])

    if title:
        ax.set_title(title)

    if labels:
        ax.set_xlabel('← West / East →')
        ax.set_ylabel('← South / North →')

    ax.invert_yaxis()
    return ax


def plot_equi(c, index, ax=None, title=None,
              labels=True,
              figsize=(16, 8), cmap='gray',
              twist=0, n_interp=512,
              interp='cubic', grid='lightgray',
              show_img=True, show_pixels=False,
              show_contour=False, **kwargs):
    """Plot projected VIMS cube image as equirectangular.

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
    img, (x, y), extent, cnt = equi_cube(c, index, n=n_interp, interp=interp)
    glon, glat = c.ground_lon, c.ground_lat

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    if show_img:
        opts = {}
        if 'alpha' in kwargs:
            opts['alpha'] = kwargs['alpha']
        if 'vmin' in kwargs:
            opts['vmin'] = kwargs['vmin']
        if 'vmax' in kwargs:
            opts['vmax'] = kwargs['vmax']

        ax.imshow(img, cmap=cmap, extent=extent, **opts)

    if show_pixels:
        ax.scatter(glon, glat, s=25, facecolors='none', edgecolors=show_pixels)

    if show_contour:
        ax.plot(*cnt, '-', color=show_contour)

    if title is None:
        title = _title(c, index)

    dlon, dlat = np.max(cnt, axis=1) - np.min(cnt, axis=1)

    if dlon > 90:
        lons = np.arange(-180, 180 + 30, 30)
    elif dlon > 30:
        lons = np.arange(-180, 180 + 10, 10)
    else:
        lons = np.arange(int(np.min(cnt[0])), int(np.max(cnt[0])) + 1)

    if dlat > 90:
        lats = np.arange(-90, 90 + 30, 30)
    elif dlat > 30:
        lats = np.arange(-90, 90 + 10, 10)
    else:
        lats = np.arange(int(np.min(cnt[1])), int(np.max(cnt[1])) + 1)

    ax.set_xticks(lons)
    ax.set_yticks(lats)
    ax.xaxis.set_major_formatter(_fmt_lon)
    ax.yaxis.set_major_formatter(_fmt_lat)

    if grid is not None:
        ax.grid(color=grid, linewidth=.75)

    if title:
        ax.set_title(title)

    if labels:
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')

    ax.set_xlim(extent[:2])
    ax.set_ylim(extent[2:])

    # Reverse axis
    ax.invert_xaxis()
    ax.invert_yaxis()
    return ax


def plot_polar(c, index, ax=None, title=None,
               figsize=(8, 8), cmap='gray',
               twist=0, n_interp=512,
               interp='cubic', grid='lightgray',
               show_img=True, show_pixels=False,
               show_contour=False, lat_min=60, **kwargs):
    """Plot projected VIMS cube image in polar view.

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
    lat_min: float, optional
        Absolute value of the minimum latitude cut-off.

    """
    img, _, extent, pix, cnt, n_pole = polar_cube(c, index, n=n_interp, interp=interp)

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    if show_img:
        opts = {}
        if 'alpha' in kwargs:
            opts['alpha'] = kwargs['alpha']
        if 'vmin' in kwargs:
            opts['vmin'] = kwargs['vmin']
        if 'vmax' in kwargs:
            opts['vmax'] = kwargs['vmax']

        ax.imshow(img, cmap=cmap, extent=extent, **opts)

    if show_pixels:
        ax.scatter(*pix, s=25, facecolors='none', edgecolors=show_pixels)

    if show_contour:
        ax.plot(*cnt, '-', color=show_contour)

    if title is None:
        title = _title(c, index)

    if grid is not None:
        kwargs = {
            'color': grid,
            'linewidth': .75,
        }

        r_max = 90 - lat_min
        r0 = 10
        r1 = np.sqrt(2) * r_max

        for t in np.arange(0, 360, 30):
            cth, sth = np.cos(np.radians(t)), np.sin(np.radians(t))
            ax.plot([(0 if t % 90 == 0 else r0) * cth, r1 * cth],
                    [(0 if t % 90 == 0 else r0) * sth, r1 * sth],
                    **kwargs)

        for r in np.arange(r0, r1 + r0, r0):
            ax.plot(*_circle(r), '-', **kwargs)

        ns = 'N' if n_pole else 'S'

        def _fmt_lat(lat):
            t_45 = (90 - lat) / np.sqrt(2)
            return -t_45, -t_45, f'\n\n{lat}°{ns}'

        for lat in np.arange(lat_min - r0, 90, r0):
            ax.text(*_fmt_lat(lat), color=kwargs['color'], rotation=45,
                    ha='center', va='center')

        t_30 = r_max / np.sqrt(3)

        ax_tr = ax.twinx().twiny()

        ax.set_xticks([-t_30, 0, t_30])
        ax.set_yticks([t_30, 0, -t_30])

        ax_tr.set_xticks([-t_30, 0, t_30])
        ax_tr.set_yticks([t_30, 0, -t_30])

        if n_pole:
            ax.set_xticklabels(['30°W', '0°', '30°E'])
            ax_tr.set_xticklabels(['150°W', '180°', '150°E'])
        else:
            ax.set_xticklabels(['150°W', '180°', '150°E'])
            ax_tr.set_xticklabels(['30°W', '0°', '30°E'])

        ax.set_yticklabels(['60°W', '90°W', '120°W'])
        ax_tr.set_yticklabels(['60°E', '90°E', '120°E'])

        ax.set_xlim(-r_max, r_max)
        ax.set_ylim(-r_max, r_max)

        ax_tr.set_xlim(-r_max, r_max)
        ax_tr.set_ylim(-r_max, r_max)

        if n_pole:
            ax_tr.invert_yaxis()

    else:
        ax.set_xticks([])
        ax.set_yticks([])

        ax.set_xlim(extent[:2])
        ax.set_ylim(extent[2:])

    if title:
        ax.set_title(title)

    # Reverse y-axis only for the north pole
    if n_pole:
        ax.invert_yaxis()

    return ax


def plot_all(c, index, **kwargs):
    """Plot the cube in all projection.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to plot.
    index: int or float
        VIMS band or wavelength to plot.

    """
    plt.figure(figsize=(20, 10))

    ax0 = plt.subplot(241)
    ax1 = plt.subplot(242)
    ax2 = plt.subplot(243)
    ax3 = plt.subplot(244)
    ax4 = plt.subplot(212)

    c.plot(index, ax=ax0, title='Camera FOV')
    c.plot(index, 'sky', ax=ax1, title='Sky projection')
    c.plot(index, 'ortho', ax=ax2, title='Orthogrpahic projection')
    c.plot(index, 'polar', ax=ax3, title='Polar projection')
    c.plot(index, 'equi', ax=ax4, title='Equirectangular')


def plot_specular(c, index, title=False, **kwargs):
    """Plot VIMS cube image.

    Parameters
    ----------
    c: pyvims.VIMS
        Cube to plot.
    index: int or float
        VIMS band or wavelength to plot.

    """
    figsize = _extract(0, 'figsize', kwargs, (12, 3))
    legend = _extract(0, 'legend', kwargs, True)

    fig = plt.figure(figsize=figsize)
    grid = plt.GridSpec(1, 3, wspace=0.2, hspace=0.3)

    ax0 = fig.add_subplot(grid[0, 0])
    ax1 = fig.add_subplot(grid[0, 1:])

    plot_img(c, index, show_specular=True, ax=ax0, show_legend=False, title=title)
    plot_spectra(c, *c.specular_sl, ax=ax1, legend=legend, title=False)
