"""ISIS table module."""

import numpy as np

from .vars import BYTE_ORDERS, FIELD_TYPES


class ISISField:
    """ISIS table field object.

    Parameters
    ----------
    pvl: PVLObject
        PVL table object.

    """

    def __init__(self, pvl):
        self.__pvl = pvl

    def __str__(self):
        return self.__pvl['Name']

    def __len__(self):
        return self.__pvl['Size']

    def __repr__(self):
        return f'<{self.__class__.__name__}> Name: `{self}`'

    @property
    def dtype(self):
        """Field data type."""
        return FIELD_TYPES[self.__pvl['Type']]


class ISISFields:
    """ISIS table fields collection.

    Parameters
    ----------
    pvl: PVLObject
        PVL table object.

    """

    def __init__(self, pvl):
        self.__pvl = pvl
        self.__fields = None
        self.__labels = None

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> Available:',
            *self.keys()])

    def __iter__(self):
        return iter(self.fields)

    def __contains__(self, key):
        return key in self.keys()

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(f'Key `{key}` not found.')

        if key in self.labels.keys():
            return self.labels[key]

        return self.fields[key]

    def _load_pvl(self):
        """Load PVL data."""
        self.__fields = {}
        self.__labels = {}
        for key, value in self.__pvl:
            if key == 'Field':
                field = ISISField(value)
                self.__fields[str(field)] = field
            else:
                self.__labels[key] = value

    @property
    def fields(self):
        """Collection of ISIS fields."""
        if self.__fields is None:
            self._load_pvl()
        return self.__fields

    @property
    def labels(self):
        """Collection of ISIS labels."""
        if self.__labels is None:
            self._load_pvl()
        return self.__labels

    def keys(self):
        """List of fields names."""
        return list(self.fields.keys()) + list(self.labels.keys())

    @property
    def names(self):
        """List of fields names."""
        names = []
        for field in self.fields.values():
            if len(field) == 1:
                names += [str(field)]
            else:
                for i in range(len(field)):
                    names += [f'{field}_{i+1}']
        return names

    @property
    def dtypes(self):
        """List of dtypes from fields."""
        dtypes = []
        for field in self.fields.values():
            dtypes += len(field) * [field.dtype]
        return dtypes


class ISISTable:
    """ISIS table object.

    Parameters
    ----------
    filename: str
        Isis cube filename.
    pvl: PVLObject
        PVL table object.

    """

    def __init__(self, filename, pvl):
        self.filename = filename
        self.__pvl = pvl
        self.__fields = None
        self.__data = None

    def __str__(self):
        return self.__pvl['Name']

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> Name: `{self}`. Fields:',
            *self.keys()
        ])

    def __int__(self):
        return self.__pvl['Bytes']

    def __len__(self):
        return self.__pvl['Records']

    def __contains__(self, key):
        return key in self.fields.keys()

    def __getitem__(self, key):
        if key not in self.fields:
            raise KeyError(f'Key `{key}` not found.')

        if key in self.fields.labels.keys():
            return self.fields[key]

        return self.data[key]

    @property
    def start(self):
        """Start byte position."""
        return self.__pvl['StartByte'] - 1

    @property
    def order(self):
        """Byte order."""
        return BYTE_ORDERS[self.__pvl['ByteOrder']]

    @property
    def fields(self):
        """Table fields."""
        if self.__fields is None:
            self.__fields = ISISFields(self.__pvl)
        return self.__fields

    def keys(self):
        """List of table keys."""
        return self.fields.keys()

    @property
    def data(self):
        """Table data content."""
        if self.__data is None:
            self.__data = self._load_data()
        return self.__data

    @property
    def dtype(self):
        """Table fields types."""
        return np.dtype({
            'names': self.fields.names,
            'formats': [self.order + dtype for dtype in self.fields.dtypes]
        })

    def _load_data(self):
        """Load ISIS table data."""
        with open(self.filename, 'rb') as f:
            f.seek(self.start)
            data = f.read(int(self))

        return np.frombuffer(data, dtype=self.dtype)


class ISISTables:
    """ISIS tables collection.

    Parameters
    ----------
    filename: str
        Isis cube filename.
    pvl: PVLObject
        PVL table object.

    """

    def __init__(self, filename, pvl):
        self.filename = filename
        self.__pvl = pvl
        self.__tables = None

    def __repr__(self):
        return '\n - '.join([
            f'<{self.__class__.__name__}> Available:',
            *self.keys()])

    def __contains__(self, key):
        return key in self.tables.keys()

    def __getitem__(self, key):
        try:
            return self.tables[key]
        except KeyError:
            raise KeyError(f'Item `{key}` not found in tables.')

    def __getattr__(self, key):
        return self[key]

    @property
    def tables(self):
        """Collection of ISIS tables."""
        if self.__tables is None:
            self.__tables = {}
            for key, value in self.__pvl:
                if key == 'Table':
                    table = ISISTable(self.filename, value)
                    self.__tables[str(table)] = table
        return self.__tables

    def keys(self):
        """List of tables names."""
        return self.tables.keys()
