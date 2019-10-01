"""Background maps module."""

import os

from matplotlib.image import imread

from ..vars import ROOT_DATA


def fname(target, inst):
    """Get file name location.

    Parameters
    ----------
    target: str
        Target name.
    inst: str
        Instrument name.

    Returns
    -------
    str
        Full path image background map.

    Raises
    ------
    FileNotFoundError
        If the map is not available.

    """
    _fname = f'{target.title()}_{inst.upper()}.jpg'
    _root = os.path.join(ROOT_DATA, 'maps')

    filename = os.path.join(_root, _fname)

    if not os.path.exists(filename):
        raise FileNotFoundError(f'Maps `{_fname}` is not available.')

    return filename


def bg_map(target, inst):
    """Get internal background map.

    Parameters
    ----------
    target: str
        Target name.
    inst: str
        Instrument name.

    Returns
    -------
    array
        Imported background image.

    """
    return imread(fname(target, inst))
