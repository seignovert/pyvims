"""Cassini module."""

import re


def img_id(fname):
    """Extract image ID from filename.

    Parameters
    ----------
    fname: str or pathlib.Path
        Input filename.

    Returns
    -------
    str
        Cassini image ID.

    Raises
    ------
    ValueError
        If the provided name is invalid.


    Examples
    --------
    >>> img_id('1487096932_1')
    '1487096932_1'

    >>> img_id('C1487096932_1_ir.cub')
    '1487096932_1'

    >>> img_id('v1487096932_1_001.qub')
    '1487096932_1_001'

    """
    img_ids = re.findall(r'\d{10}_\d+(?:_\d+)?', str(fname))

    if not img_ids:
        raise ValueError(f'File `{fname}` name does not '
                         'match the correct ID pattern.')

    return img_ids[0]
