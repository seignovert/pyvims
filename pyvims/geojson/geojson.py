"""Abstract GeoJson dict module."""

import json
from pathlib import Path


class GeoJson:
    """Abstract GeoJson dict object."""

    def __repr__(self):
        return f'<{self.__class__.__name__}> {self}'

    def __iter__(self):
        raise NotImplementedError

    def __eq__(self, other):
        return self.json == other

    @property
    def json(self):
        """JSON dump."""
        return json.dumps(dict(self))

    def save(self, fname, overwrite=False, verbose=True):
        """Export as geojson file.

        Parameters
        ----------
        fname: str
            Export file name.
        overwrite: bool, optional
            Enable file overwrite.
        verbose: bool, optional
            Enable verbose output.

        Raises
        ------
        FileExistsError
            If the file already exists and ``overwrite``
            is set to ``False``.

        """
        f = Path(fname).with_suffix('.geojson')

        if f.exists() and not overwrite:
            raise FileExistsError(str(f))

        f.write_text(self.json)

        if verbose:
            print(f'Geojson saved in `{str(f)}`.')
