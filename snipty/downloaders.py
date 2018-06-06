import logging
import os
import tempfile

import requests

logger = logging.getLogger('snipty')


class DownloaderError(Exception):
    pass


class BaseDownloader:

    # @abstractmethod
    @classmethod
    def match(cls, url: str):
        """Check if given downloader can handle this request"""
        raise NotImplementedError

    # @abstractmethod
    @classmethod
    def download(cls, url: str) -> str:
        """Should get the raw snippet content from url and return a path to temporary file or directory"""
        raise NotImplementedError


class BasicDownloader(BaseDownloader):
    """
    Basic downloader will get any file that is plain/text type and HTTP status code was 200
    """

    ACCEPTED_CONTENT_TYPE = 'text/plain'
    ACCEPTED_HTTP_STATUS = 200

    @classmethod
    def match(cls, url: str):
        return True

    @classmethod
    def _fetch_file(self, url):
        with tempfile.NamedTemporaryFile(delete=False, dir=os.environ.get('SNIPTY_TMP')) as destination_file:
            response = requests.get(url)
            if response.status_code != BasicDownloader.ACCEPTED_HTTP_STATUS:
                raise DownloaderError('could not fetch {} (HTTP{})'.format(url, response.status_code))
            if not response.headers['content-type'].startswith(BasicDownloader.ACCEPTED_CONTENT_TYPE):
                raise DownloaderError('not a {} format.'.format(BasicDownloader.ACCEPTED_CONTENT_TYPE))

            for block in response.iter_content(1024):
                destination_file.write(block)

            return destination_file.name

    @classmethod
    def download(cls, url: str):
        return cls._fetch_file(url)


class GhostbinDownloader(BasicDownloader):
    """"
    Support for ghostbin.com service

    Rewrites links to ghostbin to use raw files.
    """

    @classmethod
    def match(cls, url: str):
        return url.startswith('https://ghostbin.com/paste/')

    @classmethod
    def download(cls, url: str) -> str:
        # Use native raw support fo ghostbin
        if not url.endswith('/raw'):
            url += '/raw'

        return super().download(url)
