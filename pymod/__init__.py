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
  # TODO: report, purge, switch
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      '-s',
      '--shell',
      default=manager.shell,
      type=str,
      help='syntax of shell (default: current shell `%(default)s`)')
  parser.add_argument(
      '-u', '--use', action='append', type=str, metavar='PACKAGE')
  parser.add_argument(
      '-ne',
      '--not-expand',
      action='store_true',
      help='[not] expand environment vairable')
  parser.add_argument(
      '-i',
      '--interactive',
      action='store_true',
      help='use package [interactively]')
  # parser.add_argument('-o', '--output', type=str, metavar='FILENAME')
  parser.add_argument(
      '-a', '--avail', action='store_true', help='show available packages')
  parser.add_argument(
      '-v', '--version', action='version', version=f'pymod {__version__}')
  args = parser.parse_args()
  if args.avail:
    manager.show()
  elif args.interactive:
    interactive_mode()
  elif args.use:
    manager.use_shell(args.shell)
    manager.use(args.use, not args.not_expand)


if __name__ == '__main__':
  run_main()
