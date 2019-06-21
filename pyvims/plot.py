# -*- coding: utf-8 -*-
"""PyVIMS Plot module."""

import numpy as np

import matplotlib.pyplot as plt


def img_cube(cube, band=167, wvln=None, fig=None, ax=None, title=None,
             xyticks=True, xylabels=True, interp='bicubic'):
    """Plot VIMS cube image.

    Parameters
    ----------
    cube: pyvims.VIMS
        Cube to plot.
    band: int, optional
        VIMS band to plot.
    wvln: float, optional
        Wavelength to plot (µm).
    fig: matplotlib.figure
        Optional matplotlib figure object.
    title: str, optional
        Figure title.
    xyticks: bool, optional
        Show sample and line ticks.
    xylabels: bool, optional
        Show sample and line labels.
    interp: str, optional
        Interpolation choice (see :py:func:`pyplot.imshow` for details).

    """
    wvln = cube.getWvln(band=band, wvln=wvln)
    img = cube.getImg(wvln=wvln)

    if ax is None:
        if fig is None:
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    ax.imshow(img, cmap='gray', extent=cube.extent, interpolation=interp)

    if title is None:
        title = '%s at %.2f µm' % (cube.imgID, wvln)

    if title:
        ax.set_title(title)

    if xyticks:
        ax.set_xticks(cube.sticks)
        ax.set_yticks(cube.lticks)

    if xylabels:
        ax.set_xlabel('Sample')
        ax.set_ylabel('Line')


def spectrum_cube(cube, S=1, L=1, fig=None, ax=None,
                  title=None, xylabels=True, label=None,
                  color=None, yoffset=0, vmin=0, vmax=None,
                  wmin=None, wmax=None, vis=True, ir=True):
    """Plot VIMS cube pixel spectrum.

    Parameters
    ----------
    cube: pyvims.VIMS
        Cube to plot.
    S: integer, optional
        Pixel sample value.
    L: integer, optional
        Pixel line value.
    fig: matplotlib.figure
        Optional matplotlib figure object.
    title: str, optional
        Figure title.
    label: str, optional
        Spectrum label location.
    xylabels: bool, optional
        Show sample and line labels.
    color: str, optional
        Line spectrum color.
    yoffset: float, optional
        Offset spectrum value on the y-axis.
    vmin: float, optional
        Min I/F value on y-axis.
    vmax: float, optional
        Max I/F value on y-axis.
    wmin: float, optional
        Min wavelength value on x-axis.
    wmax: float, optional
        Max wavelength value on x-axis.
    vis: bool, optional
        Display the visible part of the spectrum.
    ir: bool, optional
        Display the infrared part of the spectrum.

    Raises
    ------
    ValueError
        If `S` and `L` don't have the same size.

    """

    _wmin, _wmax = np.infty, -np.infty
    _vmax = 0
    _legend = True if label else False

    if not isinstance(S, list):
        S = [S]

    if not isinstance(L, list):
        L = [L]

    if len(S) != len(L):
        if len(S) == 1:
            S = len(L) * [S[0]]
        elif len(L) == 1:
            L = len(S) * [L[0]]
        else:
            raise ValueError('`S` and `L` must have the same size.')

    if not isinstance(color, list):
        color = len(S) * [color]

    if not isinstance(yoffset, list):
        yoffset = len(S) * [yoffset]

    if not isinstance(label, list):
        label = len(S) * [label]

    if not isinstance(vis, list):
        vis = len(S) * [vis]

    if not isinstance(ir, list):
        ir = len(S) * [ir]

    if ax is None:
        if fig is None:
            fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    for s, l, _color, _yoffset, _label, _vis, _ir in zip(S, L, color, yoffset,
                                                         label, vis, ir):
        wvlns = np.copy(cube.wvlns)
        spectrum = cube.getSpec(S=s, L=l) + _yoffset

        if not _vis:
            wvlns[:96] = np.nan
            spectrum[:96] = np.nan

        if not _ir:
            wvlns[96:] = np.nan
            spectrum[96:] = np.nan

        if _label is None:
            _label = 'S=%i, L=%i' % (s, l)
            _legend = True

        if _color:
            ax.plot(wvlns, spectrum, '-', color=_color, label=(_label if _label else None))
        else:
            ax.plot(wvlns, spectrum, '-', label=(_label if _label else None))

        if np.nanmin(wvlns) < _wmin:
            _wmin = np.nanmin(wvlns)

        if np.nanmax(wvlns) > _wmax:
            _wmax = np.nanmax(wvlns)

        if np.nanmax(spectrum):
            _vmax = np.nanmax(spectrum)

    if title is None:
        title = cube.imgID

    if title:
        ax.set_title(cube.imgID)

    if xylabels:
        ax.set_xlabel('Wavelength (µm)')
        ax.set_ylabel('I/F')

    if _legend:
        ax.legend()

    if vmax is None:
        vmax = _vmax

    if wmin is None:
        wmin = _wmin

    if wmax is None:
        wmax = _wmax

    ax.set_ylim(vmin, vmax + .01 * (vmax - vmin))
    ax.set_xlim(wmin - .01 * (wmax - wmin), wmax + .01 * (wmax - wmin))
