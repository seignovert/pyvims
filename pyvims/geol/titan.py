"""Titan geological data module."""

from .cmap import UnitsColormap
from .data import DATA
from .units import GeolUnits
from ..planets import Titan as _Titan


class Titan(metaclass=GeolUnits):
    """Titan geological map.

    Sources
    -------
    [1] Lopes et al. (2019) - Nat. Astro. doi:10.1038/s41550-019-0917-6
    [2] MacKenzie et al. (2014) - Icarus doi:10.1016/j.icarus.2014.08.022
    [3] Combination of:
            * Titan Radar stereographic view of the North-Pole (PIA17655_).
            * Titan ISS equirectangular maps (PIA22770_).
        contours made by B. Seignovert in Sept. 2019.

    _PIA17655:: https://photojournal.jpl.nasa.gov/catalog/PIA17655
    _PIA22770:: https://photojournal.jpl.nasa.gov/catalog/PIA22770

    Note
    ----
    The geological map are stack in the following order: [1], [2], [3].

    """

    R = _Titan.radius  # Planet radius [km]

    MAP = DATA / 'Titan_geol_map.png'

    LEGEND = {
        0: 'Bassins',       # [1] Ba
        10: 'Minor_lakes',  # [3]
        11: 'Jingpo',       # [3]
        12: 'Punga_Kivu',   # [3]
        13: 'Ligeia',       # [3]
        14: 'Kraken_inf',   # [3]
        15: 'Kraken_sup',   # [3]
        25: 'Evaporites',   # [2]
        50: 'Craters',      # [1] Cr
        100: 'Dunes',       # [1] Dn
        150: 'Labyrinth',   # [1] Lb
        200: 'Hummocky',    # [1] Mt
        255: 'Plains',      # [1] Pl
    }

    CMAP = UnitsColormap({
        0: '#0f5cd7',    # Bassins
        10: '#002d9b',   # Minor lakes
        11: '#002996',   # Jingpo
        12: '#002591',   # Punga and Kivu
        13: '#00228b',   # Ligeia
        14: '#001e86',   # Kraken-inf
        15: '#001a81',   # Kraken-sup
        25: '#ff8a81',   # Evaporites
        50: '#f10017',   # Craters
        100: '#8a00a8',  # Dunes
        150: '#fd00c2',  # Labyrinth
        200: '#ffab24',  # Hummocky
        255: '#00e7a9',  # Plains
    }, name='titan_geol')
