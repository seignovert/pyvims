"""Titan geological data module."""

from .data import DATA
from .units import GeolUnits

from matplotlib.colors import ListedColormap


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

    R = 2575  # Planet radius [km]

    MAP = DATA / 'Titan_geol_map.png'

    LEGEND = {
        0: 'Bassins',       # Bassins [1]
        10: 'Minor_lakes',  # Minor lakes [3]
        11: 'Jingpo',       # Jingpo [3]
        12: 'Punga_Kivu',   # Punga and Kivu [3]
        13: 'Ligeia',       # Ligeia [3]
        14: 'Kraken_inf',   # Kraken-inf [3]
        15: 'Kraken_sup',   # Kraken-sup [3]
        25: 'Evaporites',   # Evaporites [2]
        50: 'Craters',      # Craters [1]
        100: 'Dunes',       # Dunes [1]
        150: 'Labyrinth',   # Labyrinth [1]
        200: 'Hummocky',    # Hummocky [1]
        255: 'Plains',      # Plains [1]
    }

    LOPES2019 = {
        0: 'Ba',           # Lakes [1]
        50: 'Cr',          # Craters [1]
        100: 'Dn',         # Dunes [1]
        150: 'Lb',         # Labyrinth [1]
        200: 'Mt',         # Hummocky [1]
        255: 'Pl',         # Plains [1]
    }

    LOPES2019_CMAP = ListedColormap([
        '#0f5cd7',
        '#f10017',
        '#8a00a8',
        '#fd00c2',
        '#ffab24',
        '#00e7a9',
    ])
