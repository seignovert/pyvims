"""PDS html parser."""

from html.parser import HTMLParser

from .errors import PDSError


class ReleasesParser(HTMLParser):
    """PDS releases parser object.

    Parameters
    ----------
    html: str
        HTML page content to parse.
    src: str, optional
        Link sources key (default: ``jpl``).
    keyword: str, optional
        Data keyword to extract.

    """

    def __init__(self, html, src='jpl', keyword=''):
        super().__init__()
        self.src = src.lower()
        self.keyword = keyword

        self.__last_link = None
        self.results = []

        self.feed(html)

        if not self.results:
            self.error('No links found during parsing.')

    def __repr__(self):
        return (f'<{self.__class__.__name__}> '
                f'{len(self)} link{"s" if len(self) > 1 else ""} found.')

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        return iter(self.results)

    def handle_starttag(self, tag, attrs):
        """Extract the release links.

        Search links in all with ``href`` attribute which content
        the source pattern and does not end with ``.tag.gz``.

        Parameters
        ----------
        tag: str
            Starting tag name.
        attrs: list
            Tag attributes

        """
        if tag != 'a':
            return

        for attr, val in attrs:
            if attr == 'href' and self.src in val:
                if not val.endswith('.tar.gz'):
                    self.__last_link = val
                break

    def handle_data(self, data):
        """Parse releases page data content.

        Search :py:attr:`start` and :py:attr:`stop` containing
        ``Cassini`` and ``Images`` strings.

        Parameters
        ----------
        data: string
            Data content

        """
        if self.__last_link is not None and self.keyword in data:
            self.results.append((data, self.__last_link))
            self.__last_link = None

    def error(self, message):
        """Parsing error.

        Parameters
        ----------
        message: str
            Error message

        Raises
        ------
        PDSError
            If error occurs during the parsing

        """
        raise PDSError(message)
