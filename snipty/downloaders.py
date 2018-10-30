import logging
import os
import tempfile
from urllib.parse import urlparse

import requests

logger = logging.getLogger("snipty")


class DownloaderError(Exception):
    pass


class BaseDownloader:

    # @abstractmethod
    @classmethod
    def match(cls, url: str) -> bool:
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

    ACCEPTED_CONTENT_TYPE = ["text/plain", "application/x-python"]
    ACCEPTED_HTTP_STATUS = 200

    @classmethod
    def match(cls, url: str) -> bool:
        return True

    @classmethod
    def _valid_content_type(cls, content_type: str) -> bool:
        for entry in cls.ACCEPTED_CONTENT_TYPE:
            if content_type.startswith(entry):
                return True
        return False

    @classmethod
    def _fetch_file(cls, url: str) -> str:
        with tempfile.NamedTemporaryFile(
            delete=False, dir=os.environ.get("SNIPTY_TMP")
        ) as destination_file:
            response = requests.get(url)

            if response.status_code != BasicDownloader.ACCEPTED_HTTP_STATUS:
                raise DownloaderError(
                    "could not fetch {} (HTTP{})".format(url, response.status_code)
                )

            if not cls._valid_content_type(response.headers["content-type"]):
                raise DownloaderError(
                    "not a {} format.".format(", ".join(cls.ACCEPTED_CONTENT_TYPE))
                )

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
    def match(cls, url: str) -> bool:
        return url.startswith("https://ghostbin.com/paste/")

    @classmethod
    def download(cls, url: str) -> str:
        # Use native raw support fo ghostbin
        if not url.endswith("/raw"):
            url += "/raw"

        return super().download(url)


class GistDownloader(BaseDownloader):
    """
    Support for gist.github.com via REST API v3
    """

    @classmethod
    def match(cls, url: str) -> bool:
        return urlparse(url).netloc == "gist.github.com"

    @classmethod
    def _extract_gist_id(self, url: str) -> str:
        return urlparse(url).path.split("/")[-1]

    @classmethod
    def download(cls, url: str) -> str:
        # Fetch gist from API
        api_url = "https://api.github.com/gists/{}".format(cls._extract_gist_id(url))
        response = requests.get(api_url)

        if response.status_code != 200:
            raise DownloaderError(
                "could not fetch {} (HTTP{})".format(api_url, response.status_code)
            )

        data = response.json()

        if len(data["files"]) == 1:
            # Single file gist
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, dir=os.environ.get("SNIPTY_TMP")
            ) as destination_file:
                file_key = list(data["files"].keys())[0]
                destination_file.write(data["files"][file_key]["content"])
                return destination_file.name

        elif len(data["files"]) > 1:
            # Multi file gist
            destination_directory = tempfile.mkdtemp(dir=os.environ.get("SNIPTY_TMP"))
            for file_key in data["files"]:
                file_path = os.path.join(
                    destination_directory, data["files"][file_key]["filename"]
                )
                with open(file_path, "w") as file_handler:
                    file_handler.write(data["files"][file_key]["content"])
            return destination_directory
        else:
            # Some error
            raise DownloaderError("there is no snippets in this gist")
