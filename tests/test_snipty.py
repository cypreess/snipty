import os
import tempfile

import pytest

from snipty.base import Snipty, SniptyCriticalError
from snipty.downloaders import BaseDownloader, DownloaderError


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


def test_snipty_install_package_twice():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/123.txt", name="test/snippet.py")

        with pytest.raises(SniptyCriticalError):
            snipty.install_package(
                url="http://test.url/1234.txt", name="test/snippet.py"
            )


def test_snipty_install_package_same_url():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/123.txt", name="test/snippet.py")

        with pytest.raises(SniptyCriticalError):
            snipty.install_package(
                url="http://test.url/123.txt", name="test/snippet2.py"
            )


def test_snipty_install_package_existing_path():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        with open(os.path.join(project_root, "snippet.py"), "a"):
            pass
        with pytest.raises(SniptyCriticalError):
            snipty.install_package(url="http://test.url/123.txt", name="snippet.py")


def test_snipty_install_package_with_downloader_error():
    class DummyErrorDownloader(BaseDownloader):
        @classmethod
        def match(cls, url: str) -> bool:
            return True

        @classmethod
        def download(cls, url: str) -> str:
            raise DownloaderError

    class TestSnipty(Snipty):
        SUPPORTED_DOWNLOADERS = [DummyErrorDownloader]

    with tempfile.TemporaryDirectory() as project_root:
        snipty = TestSnipty(project_root)

        with pytest.raises(SniptyCriticalError):
            snipty.install_package(url="http://test.url/123.txt", name="snippet.py")


def test_snipty_install_package_with_not_matching_downloader():
    class DummyErrorDownloader(BaseDownloader):
        @classmethod
        def match(cls, url: str) -> bool:
            return False

        @classmethod
        def download(cls, url: str) -> str:
            pass

    class TestSnipty(Snipty):
        SUPPORTED_DOWNLOADERS = [DummyErrorDownloader]

    with tempfile.TemporaryDirectory() as project_root:
        snipty = TestSnipty(project_root)

        with pytest.raises(SniptyCriticalError):
            snipty.install_package(url="http://test.url/123.txt", name="snippet.py")


def test_snipty_install_missing():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        snipty.install_package(url="http://test.url/2.txt", name="2.py")
        os.remove(os.path.join(project_root, "2.py"))
        snipty.install_missing()
        assert sorted(os.listdir(project_root)) == [
            "1.py",
            "2.py",
            "__init__.py",
            "snipty.yml",
        ]


def test_snipty_uninstall():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        assert sorted(os.listdir(project_root)) == ["1.py", "__init__.py", "snipty.yml"]
        snipty.uninstall("1.py")
        assert sorted(os.listdir(project_root)) == ["__init__.py", "snipty.yml"]
        assert_file_content(os.path.join(project_root, "snipty.yml"), "{}\n")


def test_snipty_uninstall_not_installed():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        os.remove(os.path.join(project_root, "1.py"))

        with pytest.raises(SniptyCriticalError):
            snipty.uninstall("1.py")

        assert sorted(os.listdir(project_root)) == ["__init__.py", "snipty.yml"]
        assert_file_content(
            os.path.join(project_root, "snipty.yml"), "1.py: http://test.url/1.txt\n"
        )


def test_snipty_uninstall_nonexisting_1():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        with pytest.raises(SniptyCriticalError):
            snipty.uninstall("1.py")


def test_snipty_uninstall_nonexisting_2():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        with pytest.raises(SniptyCriticalError):
            snipty.uninstall("2.py")


def test_snipty_untrack():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        assert sorted(os.listdir(project_root)) == ["1.py", "__init__.py", "snipty.yml"]
        snipty.untrack("1.py")
        assert sorted(os.listdir(project_root)) == ["1.py", "__init__.py", "snipty.yml"]
        assert_file_content(os.path.join(project_root, "snipty.yml"), "{}\n")


def test_snipty_untrack_nonexisting_1():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        with pytest.raises(SniptyCriticalError):
            snipty.untrack("1.py")


def test_snipty_untrack_nonexisting_2():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        with pytest.raises(SniptyCriticalError):
            snipty.untrack("2.py")


def test_snipty_list():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        snipty.install_package(url="http://test.url/2.txt", name="2.py")
        os.remove(os.path.join(project_root, "2.py"))
        result = snipty.list()
        assert result == {
            "installed": [
                (
                    "1.py",
                    "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
                    "http://test.url/1.txt",
                )
            ],
            "not_installed": [("2.py", "http://test.url/2.txt")],
        }


def test_check():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        assert snipty.check("1.py") == 0


def test_check_different():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        with open(os.path.join(project_root, "1.py"), "a") as f:
            f.write("diff")

        assert snipty.check("1.py") == 1


def test_check_all():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        snipty.install_package(url="http://test.url/2.txt", name="2.py")
        assert snipty.check_all() == 0


def test_check_all_1():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        with open(os.path.join(project_root, "1.py"), "a") as f:
            f.write("diff")
        snipty.install_package(url="http://test.url/2.txt", name="2.py")
        assert snipty.check_all() == 1


def test_check_all_2():
    with tempfile.TemporaryDirectory() as project_root:
        snipty = DummyDownloaderSnipty(project_root)
        snipty.install_package(url="http://test.url/1.txt", name="1.py")
        with open(os.path.join(project_root, "1.py"), "a") as f:
            f.write("diff")
        snipty.install_package(url="http://test.url/2.txt", name="2.py")
        with open(os.path.join(project_root, "2.py"), "a") as f:
            f.write("diff")
        assert snipty.check_all() == 2
