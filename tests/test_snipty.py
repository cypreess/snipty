import os
import tempfile

from snipty.base import Snipty
from snipty.downloaders import BaseDownloader


class DummyDownloader(BaseDownloader):
    @classmethod
    def match(cls, url: str) -> bool:
        return True

    @classmethod
    def download(cls, url: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            return f.name


class DummyDownloaderSnipty(Snipty):
    SUPPORTED_DOWNLOADERS = [DummyDownloader]


def assert_file_content(name, content):
    with open(name) as f:
        fcontent = f.read()
        assert fcontent == content


def test_snipty_install_package():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/123.txt", name="test/snippet.py")

        assert sorted(os.listdir(project_root)) == ["snipty.yml", "test"]
        assert sorted(os.listdir(os.path.join(project_root, "test"))) == [
            "__init__.py",
            "snippet.py",
        ]
        assert_file_content(
            os.path.join(project_root, "snipty.yml"),
            "test/snippet.py: http://test.url/123.txt\n",
        )
