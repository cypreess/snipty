import json
import os
import re
import sys
from functools import wraps

import logging

from snipty.downloaders import BasicDownloader, BaseDownloader, DownloaderError, GhostbinDownloader, GistDownloader

logger = logging.getLogger('snipty')


class NotExists(Exception):
    pass


def ensure_config_saved(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        try:
            f(self, *args, **kwargs)
        finally:
            self.store_config()

    return wrapped


class Snipty:
    """Manages whole process of tracking what is installed and calling specialized downloaders"""

    SUPPORTED_DOWNLOADERS = [GistDownloader, GhostbinDownloader, BasicDownloader]

    def __init__(self, project_root, force=False):
        self.project_root = project_root
        self._config = None
        self.force = force

    def _dispatch_url(self, url) -> BaseDownloader:
        for downloader in self.SUPPORTED_DOWNLOADERS:
            if downloader.match(url):
                return downloader
        logger.error("Error: cannot find downloader for provided url {}".format(url))
        sys.exit(4)

    def _prepare_directory(self, root_path, package_dir):
        """Create a tree of directories and place __init__.py files"""
        full_path = os.path.join(root_path, package_dir)

        os.makedirs(full_path, exist_ok=True)

        while full_path != root_path:
            init_path = os.path.join(full_path, '__init__.py')
            if not os.path.exists(init_path):
                open(init_path, 'a').close()
            full_path = os.path.dirname(full_path)

    def _install_package(self, url, name):
        if not self.force and name in self.config(create=True)['packages_names']:
            logger.warning("Snippet '{}' has been already installed.".format(name))
            return

        if not self.force and url in self.config(create=True)['packages_urls']:
            logger.error(
                "Error: Snippet '{}' has been already from the same source {}.".format(
                    self.config(create=True)['packages_urls'][url], url))
            sys.exit(3)

        if not self.force and os.path.exists(os.path.join(self.project_root, name + '.py')) or os.path.exists(
                os.path.join(self.project_root, name)):
            logger.error("Error: Cannot install snippet '{}' because destination location already exists.".format(name))

        downloader_class = self._dispatch_url(url)

        try:
            tmp_path = downloader_class.download(url=url)
        except DownloaderError as e:
            logger.error("Error: Snippet {} cannot be installed - {}.".format(name, str(e)))
            sys.exit(6)

        # tmp_path can be a single file or directory (support for snippets containing many files)

        if os.path.isdir(tmp_path):
            package_dir = name
            package_name = None
        else:
            package_dir = os.path.dirname(name)
            package_name = os.path.basename(name)

        self._prepare_directory(self.project_root, package_dir)

        if package_name is not None:
            os.rename(tmp_path, os.path.join(self.project_root, package_dir, package_name + '.py'))
        else:
            for file_name in os.listdir(tmp_path):
                os.rename(
                    os.path.join(tmp_path, file_name),
                    os.path.join(self.project_root, package_dir, file_name)
                )

        self.config(create=True)['packages_names'][name] = url
        self.config(create=True)['packages_urls'][url] = name

        logger.info('✔️ Snippet {} installed from {}'.format(name, url))

    @ensure_config_saved
    def install_package(self, url, name):
        self._install_package(url, name)

    @ensure_config_saved
    def install_from_file(self, requirements):
        for line_no, line in enumerate(requirements, 1):
            line = line.decode('utf-8').strip()

            # skip comments and empty lines
            if line.startswith('#') or not line:
                continue

            match = re.match('^(?P<name>.+)\s+from\s+(?P<url>https?://.*)$', line)
            if not match:
                logger.error('Error: Requirements file syntax error in line {}.'.format(line_no))

            self._install_package(url=match.group('url'), name=match.group('name'))

    def freeze(self):
        try:
            packages = self.config().get('packages_names', {})
            for package in sorted(packages):
                print(package, 'from', packages[package])

        except NotExists:
            logger.error('Error: Snipty was not used before in this project root path: {}'.format(self.project_root))
            sys.exit(1)

    @property
    def config_file_path(self):
        return os.path.join(self.project_root, '.snipty')

    def config(self, create=False):
        """Loads, checks and cache snipty config file"""

        if self._config is None:
            # If there is no cached config file yet then read it
            if not os.path.exists(self.config_file_path):
                if not create:
                    # Some commands like freeze should not run in directories where snipty config was not present
                    raise NotExists
                # Initiate empty config otherwise
                self._store_config({})

            # Read (or re-read) snipty config file
            with open(self.config_file_path, 'r') as f:
                self._config = json.load(f)

            # Ensure that some standard keys exists
            for key in ('packages_names', 'packages_urls'):
                if key not in self._config:
                    self._config[key] = {}

            # Clean-up config file by checking if snippets really exists on disk
            for snippet_path in list(self._config['packages_names'].keys()):  # avoid error of modifing dict in the loop
                if not (os.path.exists(os.path.join(self.project_root, snippet_path)) or os.path.exists(
                        os.path.join(self.project_root, snippet_path + '.py'))):
                    del self._config['packages_urls'][self._config['packages_names'][snippet_path]]
                    del self._config['packages_names'][snippet_path]

        return self._config

    def _store_config(self, data):
        with open(self.config_file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def store_config(self):
        try:
            config = self.config()
            self._store_config(config)
        except NotExists:
            pass
