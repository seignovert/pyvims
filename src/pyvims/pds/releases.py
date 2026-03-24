"""PDS releases."""

import os

import numpy as np

from .errors import PDSError
from .html import JPLReleaseParser, ReleasesParser
from .times import cassini_time, utc2cassini
from .vars import RELEASES_URL, ROOT_DATA
from ..cassini import img_id
from ..wget import url_exists, wget_txt


class PDS:
    """PDS releases object.

    Parameters
    ----------
    instr: str
        Instrument name.
    prefix: str, optional
        Releases prefix.
    src: str, optional
        Release source (JPL/SETI/USGS).
    fmt: str, optional
        Data format (LBL, QUB).
    update: bool, optional
        Update releases list.
    verbose: bool, optional
        Display verbose results.

    Examples
    --------
    >>> 'C1487096932_1_ir.cub' in PDS('VIMS')
    True

    >>> PDS('VIMS')['1487096932_1']
    ['covims_unks', 'covims_0006']

    """

    def __init__(self, instr, prefix='co', src='jpl', fmt='lbl',
                 update=False, verbose=True):
        self.instr = instr.lower()
        self.prefix = prefix
        self.src = src
        self.fmt = fmt.lower()
        self.update = update
        self.verbose = verbose
        self.__releases = []

        self.download() if not self.is_file or update else self.load_csv()

    def __repr__(self):
        return (f'<{self.__class__.__name__}> {self.instr.upper()}\n'
                f' - Releases: {len(self)}\n'
                f' - Source: {self.src.upper()}')

    def __len__(self):
        return len(self.__releases)

    def __contains__(self, item):
        return True if self.locate(item) else False

    def __getitem__(self, item):
        urls = self.locate(item)
        if urls:
            return urls[0] if len(urls) == 1 else urls
        raise IndexError(f'Data `{item}` was not found in {self.instr.upper()} releases.')

    @property
    def fname(self):
        """Releases file name."""
        return f'{self.prefix}{self.instr}_{self.src}_releases.csv'

    @property
    def filename(self):
        """List of releases absolute file name."""
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

    def parse_times(self, data):
        """Parse releases times based on instrument name."""
        if self.instr == 'vims':
            return utc2cassini(data)
        raise ValueError(f'Unknown parsing times for instrument: {self.instr}')

    def _fmt(self, fname):
        """Get formatted name based on file and instrument name."""
        if self.instr == 'vims':
            _id = img_id(fname)
            if self.fmt == 'lbl':
                return f'v{_id}.lbl'
            if self.fmt == 'qub':
                return f'v{_id}.qub'
        raise ValueError(f'Invalid instrument: {self.instr} with format: {self.fmt}')

    @property
    def dtype(self):
        """Date types."""
        return {
            'names': ('release', 'start', 'stop', 'url'),
            'formats': ('U25', int, int, 'U999'),
        }

    def download(self):
        """Download and parse PDS releases list.

        The list is cached in a CSV file.

        """
        if self.verbose:
            print(f'Download list of releases from `{self.url}`.')

        try:
            html = wget_txt(self.url)
            results = ReleasesParser(html, src=self.src, keyword=self._keyword)
        except PDSError:
            raise PDSError(f'No releases found in {self.url}')

        releases = []
        for data, link in results:
            start, stop = self.parse_times(data)
            release = link.split('/')[-2]
            releases.append((release, int(start), int(stop), link))

        with open(self.filename, 'w') as f:
            f.write(f'release, start, stop, url, src:{self.url}\n')
            f.write('\n'.join(
                [', '.join([str(r) for r in row]) for row in releases]))

        self.__releases = np.array(releases, dtype=self.dtype)

    def load_csv(self):
        """Load CSV file."""
        with open(self.filename, 'r') as f:
            src_url = f.readlines()[1].split(':')[1]

        if 'jpl.nasa.gov' in src_url:
            self.src = 'jpl'
        elif 'usgs.gov' in src_url:
            self.src = 'usgs'
        elif 'seti.org' in src_url:
            self.src = 'seti'
        else:
            raise ValueError(f'Data source unknown: `{src_url}`.')

        self.__releases = np.loadtxt(self.filename, delimiter=', ', skiprows=1,
                                     dtype=self.dtype)

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

    def link(self, release):
        """Get URL of the release.

        Parameters
        ----------
        release: str
            Release name.

        Returns
        -------
        str
            Link to the release based on the source data.

        Raises
        ------
        IndexError
            If the name of the release was not found in the available releases.

        """
        links = self.links[self.releases == release]
        if not links:
            raise PDSError(
                f'Release `{release}` not found in {self.src.upper()} releases.')

        return links[0] if len(links) == 1 else links

    def release(self, time):
        """Find the releases which contains the spacecraft time.

        Parameters
        ----------
        time: str or int
            Cassini time.

        Returns
        -------
        list
            List of all the releases names which overlap the input time.

        """
        t = cassini_time(time)
        return list(self.releases[(self.starts <= t) & (t <= self.stops)])

    def locate(self, fname):
        """Find the location a filename.

        Parameters
        ----------
        fname: str
            Input file name.

        Returns
        -------
        list
            List of URL where the label file is located.

        """
        urls = []
        for release in self.release(fname):
            for link in PDSRelease(self, release, update=self.update).link(fname):
                url = link + self._fmt(fname)
                if url_exists(url):
                    urls.append(url)

        return urls


class PDSRelease:
    """PDS release object.

    Parameters
    ----------
    instr: str
        Instrument name.
    name: str
        Name of the release.
    src: str, optional
        Release source (JPL/SETI/USGS).
    url: str, optional
        Location of the release.
    update: bool, optional
        Update releases list.
    verbose: bool, optional
        Display verbose results.

    """

    def __init__(self, pds, name, update=False, verbose=True):
        self._pds = pds
        self.name = name
        self.verbose = verbose
        self.url = None
        self.__folders = []

        self.download() if not self.is_file or update else self.load_csv()

    def __str__(self):
        return self.name

    def __repr__(self):
        return (f'<{self.__class__.__name__}> {self}\n'
                f' - Folders: {len(self)}\n'
                f' - Source: {self.src.upper()}')

    def __len__(self):
        return len(self.__folders)

    def __contains__(self, item):
        return True if self.link(item) else False

    def __getitem__(self, item):
        folders = self.link(item)
        if folders:
            return folders
        raise IndexError(f'Data `{item}` was not found in {self}.')

    @property
    def instr(self):
        """Release PDS instrument."""
        return self._pds.instr

    @property
    def src(self):
        """Release PDS source."""
        return self._pds.src

    @property
    def fname(self):
        """Release file name."""
        return f'{self}_{self.src}.csv'

    @property
    def filename(self):
        """Release absolute file name."""
        return os.path.join(ROOT_DATA, self.fname)

    @property
    def is_file(self):
        """Check if the file exists."""
        return os.path.exists(self.filename)

    @property
    def dtype(self):
        """Date types."""
        return {
            'names': ('folders', 'start', 'stop', 'url'),
            'formats': ('U30', int, int, 'U999'),
        }

    def download(self):
        """Download a specific release."""
        if self.verbose:
            print(f'Download release {self} from {self.src.upper()}.')

        # Get PDS url based on source
        self.url = self._pds.link(self.name)

        try:
            url = self.url + 'data/'
            html = wget_txt(url)

            if self.src == 'jpl':
                results = JPLReleaseParser(html)
            else:
                raise ValueError('Release parse is only available for JPL sources.')

        except PDSError:
            raise PDSError(f'No release folders found in {url}')

        folders = []
        for data in results:
            start, stop = self._pds.parse_times(data)
            link = url + data
            folders.append((data, int(start), int(stop), link))

        with open(self.filename, 'w') as f:
            f.write(f'start, stop, url, src:{url}\n')
            f.write('\n'.join(
                [', '.join([str(r) for r in row]) for row in folders]))

        self.__folders = np.array(folders, dtype=self.dtype)

    def load_csv(self):
        """Load CSV file."""
        with open(self.filename, 'r') as f:
            self.url = f.readlines()[1].split(':')[1]

        self.__folders = np.loadtxt(self.filename, delimiter=', ', skiprows=1,
                                    dtype=self.dtype)

    @property
    def folders(self):
        """List available folders."""
        return self.__folders['folders']

    @property
    def starts(self):
        """List available folders start IDs."""
        return self.__folders['start']

    @property
    def stops(self):
        """List available folders stop IDs."""
        return self.__folders['stop']

    @property
    def links(self):
        """List available folders links."""
        return self.__folders['url']

    def link(self, time):
        """Find the folders links which contains the spacecraft time.

        Parameters
        ----------
        time: str or int
            Cassini time.

        Returns
        -------
        list
            List of all the folders which overlap the input time.

        """
        """Find the folders which contains the spacecraft time.

        Parameters
        ----------
        time: str or int
            Cassini time.

        Returns
        -------
        list
            List of all the folders which overlap the input time.

        """
        t = cassini_time(time)
        return list(self.links[(self.starts <= t) & (t <= self.stops)])
