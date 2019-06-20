"""PyVIMS Plot module."""

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
                  color=None, yoffset=0, ymin=0, ymax=None):
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
    ymin: float, optional
        Min value on y-axis.
    ymax: float, optional
        Max value on y-axis.

    """
    wvlns = cube.wvlns
    spectrum = cube.getSpec(S=S, L=L) + yoffset

    if ax is None:
        if fig is None:
            fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    if label is None:
        label = 'S=%i, L=%i' % (S, L)

    if color:
        ax.plot(wvlns, spectrum, '-', color=color, label=label)
    else:
        ax.plot(wvlns, spectrum, '-', label=label)

    if title is None:
        title = cube.imgID

    if title:
        ax.set_title(cube.imgID)

    if xylabels:
        ax.set_xlabel('Wavelength (µm)')
        ax.set_ylabel('I/F')

    if label:
        ax.legend()

    if ymax is None:
        ymax = 1.05 * max(spectrum)

    ax.set_ylim(ymin, ymax)
