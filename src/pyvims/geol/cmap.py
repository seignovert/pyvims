"""Geological Units colormap."""

from matplotlib.colors import LinearSegmentedColormap


class UnitsColormap:
    """Units colormap.

    Parameters
    ----------
    units: dict
        Geological units colors.
    vmin: int or float, optional
        Lower bound.
    vmax: int or float, optional
        Upper bound.
    name: str, optional
        The name of the colormap.

    Returns
    -------
    matplotlib.colors.LinearSegmentedColormap
        Unevenly distributed colormap.

    """

    def __new__(cls, units, name=None, vmin=0, vmax=255):
        if not isinstance(units, dict):
            raise TypeError('Units must be `dict`')

        return LinearSegmentedColormap.from_list(name, [
            ((value - vmin) / (vmax - vmin), color)
            for value, color in units.items()])
