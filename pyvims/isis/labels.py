"""ISIS header labels module."""


class ISISLabels(dict):
    """ISIS labels collection.

    Parameters
    ----------
    pvl: PVLObject
        PVL item object.

    """

    def __init__(self, pvl):
        self.__pvl = pvl
        self.__labels = None
        self.__keys = None

    def __repr__(self):
        return f'{self.labels}'

    def __contains__(self, key):
        return key in self.keys()

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(f'Label `{key}` not found in labels.')

        if key in self.labels.keys():
            return self.labels[key]

        values = []
        for _, value in self.items():
            if isinstance(value, type(self)):
                if key in value:
                    values.append(value[key])

        if len(values) == 1:
            return values[0]

        return values

    @property
    def labels(self):
        """Collection of ISIS labels."""
        if self.__labels is None:
            self.__labels = {}
            for key, value in self.__pvl:
                if key not in ['Table', 'Label', 'History', 'OriginalLabel']:
                    if isinstance(value, dict):
                        self.__labels[key] = ISISLabels(value)
                    else:
                        self.__labels[key] = value
        return self.__labels

    def keys(self):
        """List of all labels keys."""
        if self.__keys is None:
            self.__keys = ()
            for key, value in self.items():
                self.__keys += (key,)
                if isinstance(value, ISISLabels):
                    self.__keys += value.keys()
        return self.__keys

    def values(self):
        """List of labels values."""
        return self.labels.values()

    def items(self):
        """List of labels items."""
        return self.labels.items()
