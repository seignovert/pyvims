"""VIMS Noodle module."""

from pathlib import Path

from .vims import VIMS
from .errors import VIMSError


class VIMSNoodle:
    """VIMS Noodle object."""

    def __init__(self, *cubes, root=None, channel='ir', prefix='C', suffix='', ext='cub'):
        self.cubes = (cubes, root, channel, prefix, suffix, ext)

    def __str__(self):
        return '\n - '.join([
            'Cubes:',
            *[str(cube) for cube in self.cubes]
        ])

    def __repr__(self):
        return f'<{self.__class__.__name__}> {self}'

    def __len__(self):
        return len(self.cubes)

    def __getitem__(self, item):
        return self.cubes[item] if isinstance(item, (int, tuple, slice)) else \
            self.cubes[self.cubes.index(item)]

    def __iter__(self):
        return iter(self.cubes)

    @property
    def cubes(self):
        """List of cubes in the noodle."""
        return self.__cubes

    @cubes.setter
    def cubes(self, values):
        """Set noodle list of cubes.

        Raises
        ------
        VIMSError
            If the list of cubes is empty.

        """
        cubes, root, channel, prefix, suffix, ext = values

        if not cubes or not cubes[0]:
            raise VIMSError('No cubes were provided.')

        _cubes = self._list(cubes)
        n = len(_cubes)
        _root = self._list(root, n=n)
        _channel = self._list(channel, n=n)
        _prefix = self._list(prefix, n=n)
        _suffix = self._list(suffix, n=n)
        _ext = self._list(ext, n=n)

        if not len(_root) == len(_channel) == len(_prefix) \
                == len(_suffix) == len(_ext) == n:
            raise VIMSError('All the parameter must have the same size.')

        self.__cubes = [
            VIMS(
                _cubes[i],
                root=_root[i],
                channel=_channel[i],
                prefix=_prefix[i],
                suffix=_suffix[i],
                ext=_ext[i],
            ) for i in range(n)
        ]

    @staticmethod
    def _list(values, n=1):
        """Convert values as list."""
        return n * [values] if values is None or isinstance(values, (str, Path)) else \
            values[0] if isinstance(values[0], list) else list(values)
