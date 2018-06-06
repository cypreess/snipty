import argparse
import os
import logging
import sys

from snipty.base import Snipty
from . import __VERSION__

parser = argparse.ArgumentParser(prog='snipty', description='Minimalistic package manager for snippets.')
parser.add_argument('-q', '--quiet', action='count', default=0,
                    help='Give less output. Option is additive, and can be used up to 3 times (corresponding to '
                         'WARNING, ERROR, and CRITICAL logging levels).')
parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __VERSION__,
                    help='Show version and exit.')

parser.add_argument('-p', '--path', default=os.environ.get('SNIPTY_ROOT_PATH', os.getcwd()),
                    metavar='<project root path>',
                    help='Project root path; default: SNIPTY_ROOT_PATH environment variable or current directory')

subparsers = parser.add_subparsers(title='Commands', dest='command')

parser_freeze = subparsers.add_parser('freeze', help='Freeze installed snippets')

parser_install = subparsers.add_parser('install', help='Install snippets')

parser_install.add_argument('-f', '--force', action='store_true',
                            help="Force installation even if snippet was already installed or path exists")

parser_install_group = parser_install.add_mutually_exclusive_group(required=True)

parser_install_group.add_argument('-r', '--requirement', type=argparse.FileType('rb', 0), metavar='<requirements file>',
                                  help='Install from the given requirements file.')

parser_install_group.add_argument('snippet_url', nargs='?', help='snippets url', metavar='<snippets url>')

parser_install.add_argument('snippet_name', nargs='?', metavar='<snippets name>',
                            help='snippet nape; can be a path')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('snipty')
logger.setLevel(logging.INFO)


def install(args):
    """Calls snipty logic depending on arguments"""
    im = Snipty(project_root=args.path, force=args.force)
    if args.requirement:
        im.install_from_file(args.requirement)
    elif args.snippet_name and args.snippet_url:
        im.install_package(name=args.snippet_name, url=args.snippet_url)


def freeze(args):
    """Calls snipty logic for freeze"""
    Snipty(project_root=args.path).freeze()


if __name__ == '__main__':
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
        'install': install,
        'freeze': freeze
    }[args.command](args)
