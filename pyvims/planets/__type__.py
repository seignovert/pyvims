"""Abstract planet type."""

class Planet(type):
    """Abstract Planet object."""

    MEAN_RADIUS = (None, None)                          # [km] ± err [km]
    RADII = ((None, None), (None, None), (None, None))  # [km] ± err [km]

    def __str__(cls):
        return cls.__name__

    def __repr__(cls):
        return f'<{cls.__class__.__name__}> {cls}'

    def __eq__(cls, other):
        return str(cls).lower() == other.lower()

    @property
    def radius(cls):
        """Mean radius [km]."""
        return cls.MEAN_RADIUS[0]

    @property
    def r(cls):
        """Mean radius (shortcut) [km]."""
        return cls.radius

    @property
    def radii(cls):
        """Planet RADII (a, b, c) [km]."""
        return tuple([abc[0] for abc in cls.RADII])

    @property
    def a(cls):
        """Planet a-axis radius [km]."""
        return cls.RADII[0][0]

    @property
    def b(cls):
        """Planet b-axis radius [km]."""
        return cls.RADII[1][0]

    @property
    def c(cls):
        """Planet c-axis radius [km]."""
        return cls.RADII[2][0]

    def lower(cls):
        """Planet name in lowercase."""
        return str(cls).lower()
