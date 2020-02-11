"""Enceladus planet module."""

from .__type__ import Planet


class Enceladus(metaclass=Planet):
    """Enceladus - Saturn moon.

    Sources
    -------
    * [1] Roatsch et al. 2013 - doi:10.1007/978-1-4020-9217-6_24

    """

    MEAN_RADIUS = (252.1, 0.2)  # [1]
    RADII = (
        (256.6, 0.6),  # [1]
        (251.4, 0.2),  # [1]
        (248.3, 0.2),  # [1]
    )
