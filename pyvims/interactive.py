"""Interactive module.

Note
----
In Jupyter notebook, you need to enable the `notebook`
to be able to click on the plots:

..jupyter::

    %matplotlib notebook

"""

import numpy as np

import matplotlib.pyplot as plt

from .misc.maps import MAPS


def cube_click(cube, index=2.03, figsize=(12, 12)):
    """Interactive click on cube to get pixels and spectra.

    Parameters
    ----------
    cube: pyvims.VIMS
        Input VIMS cube.
    index: int, float, str or tuple
        VIMS band or wavelength to plot.
    figsize: tuple, optional
        Figure size.

    Returns
    -------
    [pyvims.VIMSPixels, …]
        List of all the pixels clicked.

    """
    pixels = []

    fig = plt.figure(figsize=figsize)
    grid = plt.GridSpec(3, 1, wspace=0.2, hspace=0.3)

    ax0 = fig.add_subplot(grid[:-1, 0])
    ax1 = fig.add_subplot(grid[-1, 0])

    cube.plot(index, ax=ax0)

    ax1.set_xlabel(cube.wlabel)
    ax1.set_ylabel(cube.ilabel)
    ax1.set_xticks(cube.wticks)

    def on_release(event):
        if event.button == 1:
            s, l = np.round([event.xdata, event.ydata])
            pixel = cube[int(s), int(l)]
            pixels.append(pixel)

            ax0.scatter(s, l, label=f'{int(s), int(l)}')
            ax0.legend(bbox_to_anchor=(1.3, 1.05), frameon=False)
            pixel.plot(ax=ax1, title=False)

    fig.canvas.mpl_connect('button_release_event', on_release)

    return pixels

def map_click(cube, index=2.03, figsize=(12, 6),
              lon_min=0, lon_max=360,
              lat_min=-90, lat_max=90,
              bg='VIMS_ISS',
              ):
    """Interactive equirectangular projected map."""
    pixels = []

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.subplots_adjust(right=.85)

    if bg:
        bgmap = MAPS[f'{cube.target_name}_{bg}']
        ax.imshow(bgmap, extent=[180, -180, -90, 90])
        ax.imshow(bgmap, extent=[180 + 360, -180 + 360, -90, 90])

    ax.add_patch(cube.patches(color='gray', alpha=.25))

    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    ax.set_aspect('auto')
    ax.invert_xaxis()

    ax.set_xlabel('West Longitude')
    ax.set_ylabel('Latitude')

    def on_release(event):
        if event.button == 1:
            lon_w, lat = np.array([event.xdata, event.ydata])
            pixel = cube[float(lon_w), float(lat)]

            if pixel:
                pixels.append(pixel)

                color = plt.cm.tab10(len(pixels) - 1)

                ax.scatter(*pixel.lonlat, c=color,
                           label=f'{lon_w:.1f}°W, {lat:.1f}°N', s=10)
                ax.add_patch(pixel.patch(alpha=.5, color=color))
                ax.legend(bbox_to_anchor=(1.2, .75), frameon=False)

    fig.canvas.mpl_connect('button_release_event', on_release)

    return pixels
