"""VIMS plot module."""

import numpy as np

import matplotlib.pyplot as plt

from .errors import VIMSError


def plot_cube(c, *args, **kwargs):
    """Generic cube plot."""
    if not args:
        raise VIMSError('Not attribute provided: '
                        'band(s), wavelength(s), (S, L) coordinates or keyword')

    if len(args) == 1:
        if isinstance(args[0], (int, float)):
            return plot_img(c, args[0], **kwargs)

        if isinstance(args[0], tuple):
            return plot_spectrum(c, *args[0], **kwargs)


def plot_img(c, index, ax=None, title=None,
             ticks=True, labels=True, figsize=(8, 8),
             cmap='gray', interp='bicubic'):
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

    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=figsize)

    ax.imshow(c@index, cmap=cmap, extent=c.extent, interpolation=interp)

    if title is None:
        if isinstance(index, float):
            title = f'{c} at {index:.2f} µm'
        else:
            title = f'{c} on band {index}'

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
                  title=None, ticks=True, labels=True, label=None, figsize=(12, 6)):
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

    ax.plot(x, c@(S, L) + offset, label=label, color=color)

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
