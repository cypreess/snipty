import argparse
import os
import logging
import sys

from snipty.base import Snipty
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


def install(args):
    """Calls snipty logic depending on arguments"""
    im = Snipty(project_root=args.path)
    if args.snippet_name:
        im.install_package(
            name=args.snippet_name, url=args.snippet_url, force=args.force
        )
    else:
        im.install_missing(force=args.force)


def list(args):
    """Calls snipty logic for freeze"""
    Snipty(project_root=args.path).list()


def untrack(args):
    """Calls snipty logic for untrack"""
    Snipty(project_root=args.path).untrack(name=args.snippet_name)


def uninstall(args):
    """Calls snipty logic for uninstall"""
    Snipty(project_root=args.path).uninstall(name=args.snippet_name)


def check(args):
    """Calls snipty logic for check"""
    im = Snipty(project_root=args.path)
    if args.snippet_name:
        im.check(name=args.snippet_name, print_diff=args.diff)
    else:
        im.check_all(print_diff=args.diff)


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

    # Dispatch command
    {
        "install": install,
        "list": list,
        "check": check,
        "untrack": untrack,
        "uninstall": uninstall,
    }[args.command](args)
