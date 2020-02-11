"""Planets module."""

from .enceladus import Enceladus
from .titan import Titan

class Planets(type):
    """Abstract Planets object."""

    __planets = [
        Titan,
        Enceladus,
    ]

    def __len__(cls):
        return len(cls.__planets)

    def __contains__(cls, item):
        return item in cls.__planets

    def __iter__(cls):
        return iter(cls.__planets)

    def __getitem__(cls, item):
        for planet in cls:  # pylint: disable=not-an-iterable
            if planet == item:
                return planet

        raise KeyError(f'Planet `{item}` undefined.')


class PLANETS(metaclass=Planets):
    """Global Planets object."""
