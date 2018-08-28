"""Simple Environment Variable Management"""
__author__ = 'chengscott'
__version__ = '0.2'
import argparse

from .manager import Manager


def interactive_mode():
  import code
  import readline
  banner = f"""\
Pymod {__version__} Interactive Mode
Type `help(mod)` for further usage"""

  def env():
    from .manager import Manager
    mod = Manager.from_json()
    return locals()

  variables = env()
  shell = code.InteractiveConsole(locals=variables)
  shell.interact(banner=banner)


def run_main():
  manager = Manager.from_json()
  # TODO: list, purge, switch
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      '-v', '--version', action='version', version=f'pymod {__version__}')
  subparsers = parser.add_subparsers(dest='command')
  use_parser = subparsers.add_parser('use', help='use package')
  use_parser.add_argument('package', nargs='+', type=str)
  use_parser.add_argument(
      '-s',
      '--shell',
      default=manager.shell,
      type=str,
      help='syntax of shell (default: current shell `%(default)s`)')
  use_parser.add_argument(
      '-ne',
      '--not-expand',
      action='store_true',
      help='[not] expand environment vairable')
  # use_parser.add_argument('-o', '--output', type=str, metavar='FILENAME')
  subparsers.add_parser('interactive', help='use package interactively')
  avail_parser = subparsers.add_parser(
      'info', help='show and search for packages')
  avail_parser.add_argument('name', nargs='?', type=str, help='search keyword')
  args = parser.parse_args()
  if args.command == 'info':
    manager.show(args.name)
  elif args.command == 'interactive':
    interactive_mode()
  elif args.command == 'use':
    manager.use_shell(args.shell)
    manager.use(args.package, not args.not_expand)


if __name__ == '__main__':
  run_main()
