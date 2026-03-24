"""Titan planet module."""

from .__type__ import Planet


class Titan(metaclass=Planet):
    """Titan - Saturn moon.

    Sources
    -------
    * [1] Zebker et al. 2009 - doi:10.1126/science.1168905

    """

    MEAN_RADIUS = (2574.73, 0.09)  # [1]
    RADII = (
        (2574.32, 0.05),   # [1]
        (2574.36, 0.03),   # [1]
        (2574.91, 0.11),   # [1]
    )
