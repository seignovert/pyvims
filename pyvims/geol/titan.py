"""Titan geological data module."""

from .data import DATA
from .units import GeolUnits

from matplotlib.colors import ListedColormap


class Titan(metaclass=GeolUnits):
    """Titan geological map.

    Sources
    -------
    [1] Lopes et al. (2019) - Nat. Astro.
    [2] Combination of:
            * Titan Radar stereographic view of the North-Pole (PIA17655_).
            * Titan ISS equirectangular maps (PIA22770_).
        contours made by B. Seignovert in Sept. 2019.

    _PIA17655:: https://photojournal.jpl.nasa.gov/catalog/PIA17655
    _PIA22770:: https://photojournal.jpl.nasa.gov/catalog/PIA22770

    """

    R = 2575  # Planet radius [km]

    MAP = DATA / 'Titan_geol_map.png'

    LEGEND = {
        255: 'Pl',         # Plains [1]
        200: 'Mt',         # Hummocky [1]
        150: 'Lb',         # Labyrinth [1]
        100: 'Dn',         # Dunes [1]
        50: 'Cr',          # Craters [1]
        15: 'La',          # Kraken-sup [2]
        14: 'La',          # Kraken-inf [2]
        13: 'La',          # Ligeia [2]
        12: 'La',          # Punga and Kivu [2]
        11: 'La',          # Jingpo [2]
        10: 'La',          # Other lakes [2]
        0: 'Ba',           # Lakes [1]
    }

    LOPES2019 = {
        0: 'Ba',           # Bassins [1]
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

    LAKES = {
        15: 'Kraken_sup',   # Kraken-sup [2]
        14: 'Kraken_inf',   # Kraken-inf [2]
        13: 'Ligeia',       # Ligeia [2]
        12: 'Punga_kivu',   # Punga and Kivu [2]
        11: 'Jingpo',       # Jingpo [2]
        10: 'Minor_lakes',  # Minor lakes [2]
    }
