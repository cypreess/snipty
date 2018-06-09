import filecmp
import json
import logging
import os
import re
import sys
from difflib import Differ
from functools import wraps

from termcolor import colored

from snipty.downloaders import BasicDownloader, BaseDownloader, DownloaderError, GhostbinDownloader, GistDownloader

logger = logging.getLogger('snipty')


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


class Snipty:
    """Manages whole process of tracking what is installed and calling specialized downloaders"""

    SUPPORTED_DOWNLOADERS = [GistDownloader, GhostbinDownloader, BasicDownloader]

    def __init__(self, project_root, force=False):
        self.project_root = project_root
        self._config = None
        self.force = force

    # Helpers

    def _dispatch_url(self, url) -> BaseDownloader:
        """Dispatch which downloader to use for a given URL"""

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

    def _requirements_file_parser(self, file):
        """Parses requirements file format: `<snippet path/name> from <url>\n...`"""
        for line_no, line in enumerate(file, 1):
            line = line.decode('utf-8').strip()
            # skip comments and empty lines
            if line.startswith('#') or not line:
                continue

            match = re.match('^(?P<name>.+)\s+from\s+(?P<url>https?://.*)$', line)

            if not match:
                logger.error('Error: Requirements file syntax error in line {}.'.format(line_no))
                sys.exit(7)

            yield match.group('name'), match.group('url')

    # Command: install

    def _install_package(self, url, name):
        if not self.force and name in self.config(create=True)['packages_names']:
            logger.warning("Snippet '{}' has been already installed.".format(name))
            return

        if not self.force and url in self.config(create=True)['packages_urls']:
            logger.error(
                "Error: Snippet '{}' has been already from the same source {}.".format(
                    self.config(create=True)['packages_urls'][url], url))
            sys.exit(3)

        if not self.force and (os.path.exists(os.path.join(self.project_root, name + '.py')) or os.path.exists(
                os.path.join(self.project_root, name))):
            logger.error("Error: Cannot install snippet '{}' because destination location already exists.".format(name))
            sys.exit(3)

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
    def install_from_file(self, requirements_file):
        for name, url in self._requirements_file_parser(requirements_file):
            self._install_package(name=name, url=url)

    # Command: Freeze

    def freeze(self):
        try:
            packages = self.config().get('packages_names', {})
            for package in sorted(packages):
                print(package, 'from', packages[package])

        except ConfigNotExists:
            logger.error('Error: Snipty was not used before in this project root path: {}'.format(self.project_root))
            sys.exit(1)

    # Command: Check

    def _print_diff(self, old_path, new_path):
        d = Differ()

        with open(old_path, 'r') as old_file:
            with open(new_path, 'r') as new_file:

                old_content = old_file.read()
                new_content = new_file.read()

                result = list(d.compare(old_content.split('\n'), new_content.split('\n')))

                for line in result:
                    if line.startswith('+ '):
                        print(colored(line, 'green'), file=sys.stderr)
                    elif line.startswith('- '):
                        print(colored(line, 'red'), file=sys.stderr)
                    else:
                        print(line, file=sys.stderr)

    def _check_package(self, name: str, url: str, print_diff: bool = False) -> int:
        try:

            if name not in self.config()['packages_names']:
                logger.warning('❌ Snippet {} is not installed.'.format(name))
                return 1

            downloader_class = self._dispatch_url(url)

            try:
                tmp_path = downloader_class.download(url=url)
            except DownloaderError as e:
                logger.error("Error: Snippet {} cannot be checked - {}.".format(name, str(e)))
                sys.exit(1)

            snippet_path = os.path.join(self.project_root, name)

            if os.path.isdir(tmp_path) and os.path.isdir(snippet_path):
                # Compare two directories

                files_changed_sum = 0

                result = filecmp.dircmp(snippet_path, tmp_path)

                if result.diff_files or result.right_only:

                    files_of_interest = result.same_files + result.diff_files + result.right_only
                    files_of_interest.sort()

                    for f in files_of_interest:
                        if f in result.same_files:
                            logger.info('✔ Snippet {} file {} did not changed.'.format(name, f))
                        elif f in result.diff_files:
                            logger.info('❌ Snippet {} file {} has changed.'.format(name, f))
                            files_changed_sum += 1
                            if print_diff:
                                self._print_diff(
                                    os.path.join(snippet_path, f),
                                    os.path.join(tmp_path, f),
                                )
                        elif f in result.right_only:
                            files_changed_sum += 1
                            logger.info('❌ Snippet {} file {} is not present.'.format(name, f))
                if files_changed_sum > 0:
                    return 1

            elif os.path.isfile(tmp_path) and os.path.isfile(snippet_path + '.py'):
                # Compare two files

                if not filecmp.cmp(snippet_path + '.py', tmp_path, shallow=False):
                    logger.warning('❌ Snippet {} has changed.'.format(name))
                    if print_diff:
                        self._print_diff(snippet_path + '.py', tmp_path)
                    return 1
            else:
                # Mismatch of types file-dir
                logger.warning('❌ Snippet {} has changed between single and multi file.'.format(name))
                return 1

            logger.info('✔ Snippet {} present and up to date.'.format(name))
            return 0

        except ConfigNotExists:
            logger.error('Error: Snipty was not used before in this project root path: {}'.format(self.project_root))
            sys.exit(1)

    def check(self, name: str, url: str, print_diff=False):
        """Check for single package"""
        exit_status = self._check_package(name=name, url=url, print_diff=print_diff)
        sys.exit(exit_status)

    def check_from_file(self, requirements_file, print_diff=False):
        """Will return exit status equal to number of differences found"""

        exit_status = 0
        for name, url in self._requirements_file_parser(requirements_file):
            exit_status += self._check_package(name=name, url=url, print_diff=print_diff)
        sys.exit(exit_status)

    # Config helpers

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
                    raise ConfigNotExists
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
        except ConfigNotExists:
            pass
