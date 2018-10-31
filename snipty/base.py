import filecmp
import hashlib
import shutil
from typing import Union

import yaml
import logging
import os
import sys
from difflib import Differ
from functools import wraps

from termcolor import colored

from snipty.downloaders import (
    BasicDownloader,
    BaseDownloader,
    DownloaderError,
    GhostbinDownloader,
    GistDownloader,
)

logger = logging.getLogger("snipty")


class ConfigNotExists(Exception):
    pass


def ensure_config_saved(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        try:
            f(self, *args, **kwargs)
        finally:
            self.store_config()

    return wrapped


def ensure_config_exists(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        try:
            f(self, *args, **kwargs)
        except ConfigNotExists:
            logger.error(
                "Error: Snipty was not used before in this project root path: {}".format(
                    self.project_root
                )
            )
            sys.exit(1)

    return wrapped


class Snipty:
    """Manages whole process of tracking what is installed and calling specialized downloaders"""

    SUPPORTED_DOWNLOADERS = [GistDownloader, GhostbinDownloader, BasicDownloader]

    def __init__(self, project_root):
        self.project_root = project_root
        self._config = None

    # Helpers

    def _get_package_full_path(self, name):
        return os.path.join(self.project_root, name)

    def _dispatch_url(self, url) -> BaseDownloader:
        """Dispatch which downloader to use for a given URL"""

        for downloader in self.SUPPORTED_DOWNLOADERS:
            if downloader.match(url):
                return downloader
        logger.error("Error: cannot find downloader for provided url {}".format(url))
        sys.exit(4)

    def _prepare_directory(self, root_path, package_dir, create_init_py=False):
        """Create a tree of directories and place __init__.py files"""
        full_path = os.path.join(root_path, package_dir)

        os.makedirs(full_path, exist_ok=True)

        while full_path != root_path:
            if create_init_py:
                init_path = os.path.join(full_path, "__init__.py")
                if not os.path.exists(init_path):
                    open(init_path, "a").close()
            full_path = os.path.dirname(full_path)

    # Command: install

    def _install_package(self, url: str, name: str, force: bool = False):
        """
        Installs single package from url
        """
        if not force and name in self.config(create=True):
            logger.warning("Snippet '{}' has been already installed.".format(name))
            return

        if not force and url in self.config(create=True).values():
            logger.error(
                "Error: Snippet from this url {} was already installed.".format(url)
            )
            sys.exit(3)

        if not force and (
            os.path.exists(os.path.join(self.project_root, name))
            or os.path.exists(os.path.join(self.project_root, name))
        ):
            logger.error(
                "Error: Cannot install snippet '{}' because destination location "
                "already exists (use --force to override).".format(name)
            )
            sys.exit(3)

        downloader_class = self._dispatch_url(url)

        try:
            tmp_path = downloader_class.download(url=url)
        except DownloaderError as e:
            logger.error(
                "Error: Snippet {} cannot be installed - {}.".format(name, str(e))
            )
            sys.exit(6)

        # tmp_path can be a single file or directory (support for snippets containing many files)

        if os.path.isdir(tmp_path):
            package_dir = name
            package_name = None
        else:
            package_dir = os.path.dirname(name)
            package_name = os.path.basename(name)

        self._prepare_directory(
            self.project_root, package_dir, create_init_py=name.endswith(".py")
        )

        if package_name is not None:
            os.rename(
                tmp_path, os.path.join(self.project_root, package_dir, package_name)
            )
        else:
            for file_name in os.listdir(tmp_path):
                os.rename(
                    os.path.join(tmp_path, file_name),
                    os.path.join(self.project_root, package_dir, file_name),
                )

        self.config(create=True)[name] = url

        logger.info("✔️ Snippet {} installed from {}".format(name, url))

    @ensure_config_saved
    def install_package(self, url, name, force=False):
        self._install_package(url, name, force=force)

    def _package_is_installed(self, name: str) -> bool:
        fname = os.path.join(self.project_root, name)
        return os.path.isfile(fname)

    @ensure_config_exists
    @ensure_config_saved
    def install_missing(self, force=False):
        installed_anything = False
        for name, url in self.config().items():
            if force or not self._package_is_installed(name):
                self._install_package(name=name, url=url, force=True)
                installed_anything = True

        if not installed_anything:
            print("No missing snippets to install!")

    # Command: List

    def _package_checksum(self, path: str) -> Union[str, None]:
        fname = os.path.join(self.project_root, path)
        h = hashlib.sha1()

        if os.path.isfile(fname):
            with open(fname, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    h.update(chunk)
            return h.hexdigest()

        elif os.path.isdir(fname):
            for package_file in os.listdir(fname):
                with open(os.path.join(fname, package_file), "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        h.update(chunk)
            return h.hexdigest()
        else:
            return None

    @ensure_config_exists
    def list(self):
        not_installed = []
        for package, url in self.config().items():
            package_hash = self._package_checksum(package)
            if package_hash is None:
                not_installed.append((package, url))
            else:
                print(package, package_hash, url, sep="\t")
        if not_installed:
            print(
                "\n! Following packages are NOT installed in the codebase"
                " (you can install them running by $ snipty install)"
            )
            for package, url in not_installed:
                print(package, url, sep="\t")

    # Command: Uninstall

    @ensure_config_exists
    @ensure_config_saved
    def uninstall(self, name: str):
        if name not in self.config():
            logger.warning("❌ Snippet {} does not exists.".format(name))
            sys.exit(1)

        if not os.path.exists(self._get_package_full_path(name)):
            logger.warning(
                "❌ Snippet {} is not installed. You can still untrack it.".format(name)
            )
            sys.exit(1)

        shutil.rmtree(self._get_package_full_path(name))

        del self.config()[name]
        logger.info("✔ Snippet {} has been uninstalled.".format(name))

    # Command: Untrack

    @ensure_config_exists
    @ensure_config_saved
    def untrack(self, name: str):
        if name not in self.config():
            logger.warning("❌ Snippet {} does not exists.".format(name))
            sys.exit(1)

        del self.config()[name]
        logger.info("✔ Snippet {} has been untracked.".format(name))

    # Command: Check

    def _print_diff(self, old_path, new_path):
        d = Differ()

        with open(old_path, "r") as old_file:
            with open(new_path, "r") as new_file:

                old_content = old_file.read()
                new_content = new_file.read()

                result = list(
                    d.compare(old_content.split("\n"), new_content.split("\n"))
                )

                for line in result:
                    if line.startswith("+ "):
                        print(colored(line, "green"), file=sys.stderr)
                    elif line.startswith("- "):
                        print(colored(line, "red"), file=sys.stderr)
                    else:
                        print(line, file=sys.stderr)

    def _check_package(self, name: str, print_diff: bool = False) -> int:
        try:

            if name not in self.config():
                logger.warning("❌ Snippet {} is not installed.".format(name))
                return 1

            url = self.config()[name]

            downloader_class = self._dispatch_url(url)

            try:
                tmp_path = downloader_class.download(url=url)
            except DownloaderError as e:
                logger.error(
                    "Error: Snippet {} cannot be checked - {}.".format(name, str(e))
                )
                sys.exit(1)

            snippet_path = os.path.join(self.project_root, name)

            if os.path.isdir(tmp_path) and os.path.isdir(snippet_path):
                # Compare two directories

                files_changed_sum = 0

                result = filecmp.dircmp(snippet_path, tmp_path)

                if result.diff_files or result.right_only:

                    files_of_interest = (
                        result.same_files + result.diff_files + result.right_only
                    )
                    files_of_interest.sort()

                    for f in files_of_interest:
                        if f in result.same_files:
                            logger.info(
                                "✔ Snippet {} file {} did not changed.".format(name, f)
                            )
                        elif f in result.diff_files:
                            logger.info(
                                "❌ Snippet {} file {} has changed.".format(name, f)
                            )
                            files_changed_sum += 1
                            if print_diff:
                                self._print_diff(
                                    os.path.join(snippet_path, f),
                                    os.path.join(tmp_path, f),
                                )
                        elif f in result.right_only:
                            files_changed_sum += 1
                            logger.info(
                                "❌ Snippet {} file {} is not present.".format(name, f)
                            )
                if files_changed_sum > 0:
                    return 1

            elif os.path.isfile(tmp_path) and os.path.isfile(snippet_path):
                # Compare two files

                if not filecmp.cmp(snippet_path, tmp_path, shallow=False):
                    logger.warning("❌ Snippet {} has changed.".format(name))
                    if print_diff:
                        self._print_diff(snippet_path, tmp_path)
                    return 1
            else:
                # Mismatch of types file-dir
                logger.warning(
                    "❌ Snippet {} has changed between single and multi file.".format(
                        name
                    )
                )
                return 1

            logger.info("✔ Snippet {} present and up to date.".format(name))
            return 0

        except ConfigNotExists:
            logger.error(
                "Error: Snipty was not used before in this project root path: {}".format(
                    self.project_root
                )
            )
            sys.exit(1)

    @ensure_config_exists
    def check(self, name: str, print_diff=False):
        """Check for single package"""

        exit_status = self._check_package(name=name, print_diff=print_diff)
        sys.exit(exit_status)

    def check_all(self, print_diff=False):
        """Will return exit status equal to number of differences found"""

        exit_status = 0
        for name in self.config():
            exit_status += self._check_package(name=name, print_diff=print_diff)
        sys.exit(exit_status)

    # Config helpers

    @property
    def config_file_path(self):
        return os.path.join(self.project_root, "snipty.yml")

    def config(self, create: bool = False) -> dict:
        """Loads, checks and cache snipty config file"""

        if self._config is None:
            # If there is no cached config file yet then read it
            if not os.path.exists(self.config_file_path):
                if not create:
                    # Some commands should not run in directories where snipty config was not present
                    raise ConfigNotExists
                # Initiate empty config otherwise
                self._store_config({})

            # Read (or re-read) snipty config file
            with open(self.config_file_path, "r") as f:
                self._config = yaml.load(f)

        return self._config

    def _store_config(self, data):
        with open(self.config_file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def store_config(self):
        try:
            config = self.config()
            self._store_config(config)
        except ConfigNotExists:
            pass
