"""Simple Environment Variable Management"""
__author__ = 'chengscott'
__version__ = '0.1'
import argparse
import json
import os
from os import environ as env
import sys

from .shell import USE_SHELL
from .cli import interactive_mode

__KEYWORDS = {}


def load_config(config):
  ret = {}
  search_path = ['/usr/local/etc/pymod', '~/.config/pymod', '']
  for path in search_path:
    try:
      filename = os.path.join(os.path.expanduser(path), config)
      with open(filename) as f:
        ret.update(json.load(f))
    except FileNotFoundError:
      pass
  return ret


def main(PKG, shell, pkgs, expand):
  HOME_PATH = env.get('HOME', '')
  if shell not in USE_SHELL:
    sys.exit(f'`{shell}` is not a supported shell')
  use_shell = USE_SHELL[shell]
  from collections import defaultdict
  path = defaultdict(list)
  for pkg in pkgs:
    prefix = PKG[pkg].get('__prefix', '')
    for var, val in PKG[pkg].items():
      if not var.startswith('__') or var in ['__cmd']:
        if isinstance(val, list):
          path[var].extend([v.format(PREFIX=prefix) for v in val])
        else:
          path[var].append(val.format(PREFIX=prefix))
  if '__cmd' in path:
    print(*path['__cmd'], sep='\n')
    path.pop('__cmd')
  evars = [(var, ':'.join(vals)) for var, vals in path.items()
           if not var.startswith('__')]
  if expand:
    evars = [(var, val.format(HOME=HOME_PATH), env.get(var, ''))
             for var, val in evars]
  else:
    evars = [(var, val.format(HOME='$HOME'), f'${var}') for var, val in evars]
  use_shell(evars)


def list_packages(PKG, avail):
  pkgs = {pkg: ', '.join(PKG[pkg].get('__keywords', '')) for pkg in PKG}
  pkgs = {k: f'({v})' if v else '' for k, v in pkgs.items()}
  print('\n'.join([f'{k} {v}' for k, v in pkgs.items()]))


def preprocess_meta():
  PKG = load_config('pkg.json')
  meta_pkg = load_config('meta.json')
  for pkg in PKG:
    if '__meta' in PKG[pkg]:
      meta = PKG[pkg]['__meta']
      PKG[pkg].update(meta_pkg[meta])
      PKG[pkg].pop('__meta')
  return PKG


def valid_use(pkg):
  if pkg in __KEYWORDS:
    return __KEYWORDS[pkg]
  raise argparse.ArgumentTypeError(f'Invalid Package Name `{pkg}`')


def run_main():
  PKG = preprocess_meta()
  __KEYWORDS.update(
      {key: pkg
       for pkg in PKG for key in PKG[pkg].get('__keywords', {})})
  __KEYWORDS.update({pkg: pkg for pkg in PKG})
  current_shell = os.path.basename(env.get('SHELL', 'bash'))
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      '-s',
      '--shell',
      default=current_shell,
      type=str,
      help='syntax of shell (default: current shell `%(default)s`)')
  parser.add_argument(
      '-u', '--use', action='append', type=valid_use, metavar='PACKAGE')
  #parser.add_argument(
  #    '--purge', action='append', type=valid_use, metavar='PACKAGE')
  #parser.add_argument(
  #    '-s', '--switch', action='append', type=valid_use, metavar='PACKAGE')
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
    list_packages(PKG, args.avail)
  elif args.interactive:
    pkgs = interactive_mode(__KEYWORDS)
    main(PKG, args.shell, pkgs, not args.not_expand)
  elif args.use:
    main(PKG, args.shell, args.use, not args.not_expand)


if __name__ == '__main__':
  run_main()
