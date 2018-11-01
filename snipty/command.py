import argparse
import os
import logging
import sys

from snipty.base import Snipty, SniptyCriticalError
from . import __VERSION__

parser = argparse.ArgumentParser(
    prog="snipty", description="Minimalistic package manager for snippets."
)
parser.add_argument(
    "-q",
    "--quiet",
    action="count",
    default=0,
    help="Give less output. Option is additive, and can be used up to 3 times (corresponding to "
    "WARNING, ERROR, and CRITICAL logging levels).",
)
parser.add_argument(
    "-V",
    "--version",
    action="version",
    version="%(prog)s " + __VERSION__,
    help="Show version and exit.",
)

parser.add_argument(
    "-p",
    "--path",
    default=os.environ.get("SNIPTY_ROOT_PATH", os.getcwd()),
    metavar="<project root path>",
    help="Project root path; default: SNIPTY_ROOT_PATH environment variable or current directory",
)

subparsers = parser.add_subparsers(title="Commands", dest="command")

parser_untrack = subparsers.add_parser(
    "untrack", help="Stop tracking snippet file but do not remove it from codebase"
)
parser_untrack.add_argument(
    "snippet_name", metavar="<snippets name>", help="snippet name; can be a path"
)

parser_uninstall = subparsers.add_parser(
    "uninstall", help="Remove snippet from codebase"
)
parser_uninstall.add_argument(
    "snippet_name", metavar="<snippets name>", help="snippet name; can be a path"
)

parser_check = subparsers.add_parser("check", help="Check for snippets changes")

parser_check.add_argument(
    "-d", "--diff", action="store_true", help="Display diff results"
)

parser_check.add_argument(
    "snippet_name",
    nargs="?",
    metavar="<snippets name>",
    help="snippet name; can be a path",
)

parser_list = subparsers.add_parser("list", help="Freeze installed snippets")

parser_install = subparsers.add_parser("install", help="Install snippets")

parser_install.add_argument(
    "-f",
    "--force",
    action="store_true",
    help="Force installation even if snippet was already installed or path exists",
)

parser_install.add_argument(
    "snippet_name",
    nargs="?",
    metavar="<snippets name>",
    help="snippet name; can be a path",
)

parser_install.add_argument(
    "snippet_url", nargs="?", help="snippets url", metavar="<snippets url>"
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("snipty")
logger.setLevel(logging.INFO)


class SniptyCommand:
    def __init__(self, args):
        self.args = args
        self.snipty = Snipty(project_root=self.args.path)

    def dispatch(self):
        getattr(self, self.args.command)(self.args)

    def install(self, args):
        """Calls snipty logic depending on arguments"""
        if args.snippet_name:
            self.snipty.install_package(
                name=args.snippet_name, url=args.snippet_url, force=args.force
            )
        else:
            self.snipty.install_missing(force=args.force)

    def list(self, args):
        """Calls snipty logic for freeze"""
        list_result = self.snipty.list()

        for package, checksum, url in list_result["installed"]:
            print(package, checksum, url, sep="\t")

        if list_result["not_installed"]:
            print(
                "\n! Following packages are NOT installed in the codebase"
                " (you can install them running by $ snipty install)"
            )
            for package, url in list_result["not_installed"]:
                print(package, url, sep="\t")

    def untrack(self, args):
        """Calls snipty logic for untrack"""
        self.snipty.untrack(name=args.snippet_name)

    def uninstall(self, args):
        """Calls snipty logic for uninstall"""
        self.snipty.uninstall(name=args.snippet_name)

    def check(self, args):
        """Calls snipty logic for check"""
        if args.snippet_name:
            exit = self.snipty.check(name=args.snippet_name, print_diff=args.diff)
        else:
            exit = self.snipty.check_all(print_diff=args.diff)

        sys.exit(exit)


if __name__ == "__main__":
    args = parser.parse_args()

    if args.command is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.quiet == 1:
        logger.setLevel(logging.WARNING)

    elif args.quiet == 2:
        logger.setLevel(logging.ERROR)

    elif args.quiet >= 3:
        logger.setLevel(logging.CRITICAL)

    try:
        SniptyCommand(args).dispatch()
    except SniptyCriticalError as e:
        sys.exit(e.code)
