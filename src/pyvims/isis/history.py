"""ISIS history object module."""

from pathlib import Path

from pvl import loads as pvl_loader


class ISISHistory:
    """ISIS history object.

    Parameters
    ----------
    filename: str
        Isis cube filename.
    pvl: PVLObject
        PVL table object.

    """

    def __init__(self, filename, pvl):
        self.filename = Path(filename)
        self.__pvl = pvl
        self.__history = None

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}>',
            *self.keys()])

    def __contains__(self, key):
        return key in self.history.keys()

    def __getitem__(self, key):
        try:
            return self.history[key]
        except KeyError:
            raise KeyError(f'Item `{key}` not found in history.')

    def __getattr__(self, key):
        return self[key]

    def __len__(self):
        return len(self.history)

    def __int__(self):
        return self.__pvl['Bytes']

    def keys(self):
        """List of history names."""
        return self.history.keys()

    @property
    def start(self):
        """Start byte position."""
        return self.__pvl['StartByte'] - 1

    @property
    def history(self):
        """Collection of ISIS history."""
        if self.__history is None:
            self.__history = self._load_data()
        return self.__history

    def _load_data(self):
        """Load history data."""
        with self.filename.open('rb') as f:
            f.seek(self.start)
            data = f.read(int(self))

        return pvl_loader(data)
