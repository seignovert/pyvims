"""PDS releases."""

import os

import numpy as np

from .errors import PDSError
from .html import ReleasesParser
from .times import cassini_time, utc2cassini
from .vars import RELEASES_URL, ROOT_DATA
from ..wget import wget_txt


class PDS:
    """PDS releases object.

    Parameters
    ----------
    instr: str
        Instrument name.
    prefix: str, optional
        Releases prefix.

    Examples
    --------
    >>> 'C1487096932_1_ir.cub' in PDS('VIMS')
    True

    >>> PDS('VIMS')['1487096932_1']
    ['covims_unks', 'covims_0006']

    """

    def __init__(self, instr, prefix='co', src='jpl', update=False, verbose=True):
        self.instr = instr.lower()
        self.prefix = prefix
        self.src = src
        self.verbose = verbose
        self.__releases = []

        self.create_csv() if not self.is_file or update else self.load_csv()

    def __repr__(self):
        return (f'<{self.__class__.__name__}> '
                f'{len(self)} {self.instr.upper()} releases.\n'
                f' - Source: `{self.src.upper()}`')

    def __len__(self):
        return len(self.__releases)

    def __contains__(self, item):
        return True if self.contains(item) else False

    def __getitem__(self, item):
        releases = self.contains(item)
        if releases:
            return releases
        raise IndexError(f'Data `{item}` was not found in {self.instr.upper()} releases.')

    @property
    def fname(self):
        """Release file name."""
        return f'{self.prefix}{self.instr}_{self.src}_releases.csv'

    @property
    def filename(self):
        """List of release filename."""
        return os.path.join(ROOT_DATA, self.fname)

    @property
    def is_file(self):
        """Check if the file exists."""
        return os.path.exists(self.filename)

    @property
    def url(self):
        """Releases location based on instrument name."""
        return f'{RELEASES_URL}/{self.instr}.html'

    @property
    def _keyword(self):
        """Parser keyword based on instrument name."""
        if self.instr == 'vims':
            return 'Raw cube data'
        raise ValueError(f'Unknown parsing keyword for instrument: {self.instr}')

    def _times(self, data):
        """Parse releases times based on instrument name."""
        if self.instr == 'vims':
            return utc2cassini(data)
        raise ValueError(f'Unknown parsing times for instrument: {self.instr}')

    def download(self):
        """Get parsed HTML release."""
        if self.verbose:
            print(f'Download list of releases from `{self.url}`.')

        results = ReleasesParser(wget_txt(self.url), src=self.src, keyword=self._keyword)

        if not results:
            raise PDSError(f'Not releases found in {self.url}')

        self.__releases = []
        for data, link in results:
            start, stop = self._times(data)
            release = link.split('/')[-2]
            self.__releases.append([release, int(start), int(stop), link])

    def create_csv(self):
        """Download and save releases list in csv file."""
        self.download()

        with open(self.filename, 'w') as f:
            f.write(f'release, start, stop, url, src:{self.url}\n')
            f.write('\n'.join(
                [', '.join([str(r) for r in row]) for row in self.__releases]))

    def load_csv(self):
        """Load CSV file."""
        with open(self.filename, 'r') as f:
            url = f.readlines()[1].split(', ')[3]

        if 'jpl.nasa.gov' in url:
            self.src = 'jpl'
        elif 'usgs.gov' in url:
            self.src = 'usgs'
        elif 'seti.org' in url:
            self.src = 'seti'
        else:
            raise ValueError(f'Data source unknown: `{url}`.')

        self.__releases = np.loadtxt(self.filename, delimiter=', ', skiprows=1,
                                     dtype={'names': ('release', 'start', 'stop', 'url'),
                                            'formats': ('U25', int, int, 'U999')})

    @property
    def releases(self):
        """List available releases."""
        return self.__releases['release']

    @property
    def starts(self):
        """List available releases start IDs."""
        return self.__releases['start']

    @property
    def stops(self):
        """List available releases stop IDs."""
        return self.__releases['stop']

    @property
    def links(self):
        """List available releases links."""
        return self.__releases['url']

    def contains(self, time):
        """Find the releases which contains the spacecraft time.

        Parameters
        ----------
        time: str or int
            Cassini time.

        """
        t = cassini_time(time)
        return list(self.releases[(self.starts <= t) & (t <= self.stops)])
