"""PyVIMS Plot module."""

import matplotlib.pyplot as plt


def img_cube(cube, band=167, wvln=None, fig=None, ax=None, title=None,
              ticks=True, labels=True):
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
    ticks: bool, optional
        Show sample and line ticks.
    labels: bool, optional
        Show sample and line labels.

    """
    wvln = cube.getWvln(band=band, wvln=wvln)
    img = cube.getImg(wvln=wvln)

    if ax is None:
        if fig is None:
            fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    ax.imshow(img, cmap='gray', extent=cube.extent, interpolation='bicubic')

    if title is None:
        title = '%s at %.2f µm' % (cube.imgID, wvln)

    if title:
        ax.set_title(title)

    if ticks:
        ax.set_xticks(cube.sticks)
        ax.set_yticks(cube.lticks)

    if labels:
        ax.set_xlabel('Sample')
        ax.set_ylabel('Line')
