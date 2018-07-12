#!/usr/bin/env python3.6
"""Simple Environment Variable Management
"""
import argparse
import difflib
import json
import os
from os import environ as env
import sys


def load_config(config):
  ret = {}
  search_path = ['/usr/local/etc/pmod', '~/.config/pmod', '']
  for path in search_path:
    try:
      filename = os.path.join(os.path.expanduser(path), config)
      with open(filename) as f:
        ret.update(json.load(f))
    except FileNotFoundError:
      pass
  return ret


HOME_PATH = env.get('HOME', '')
PKG = load_config('pkg.json')
META_PKG = load_config('meta.json')
KEYWORDS = {key: pkg for pkg in PKG for key in PKG[pkg].get('__keywords', {})}


def use_fish(evars):
  for var, val, old_val in evars:
    if var == 'PATH':
      new_val = ' '.join(val.split(':') + old_val.split(':'))
    else:
      new_val = ':'.join(filter(None, [val, old_val]))
    print(f'set -x {var} {new_val};')


def use_bash(evars):
  for var, val, old_val in evars:
    new_val = ':'.join(filter(None, [val, old_val]))
    print(f'export {var}={new_val}')


USE_SHELL = {
    'bash': use_bash,
    'fish': use_fish,
    'zsh': use_bash,
}


def main(shell, pkgs, expand):
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


def interactive_mode():
  pkgs = []
  print(f'# Input packages until EOF', file=sys.stderr)
  while True:
    print('> ', end='', file=sys.stderr)
    try:
      pkg = input()
      pkg = [p for ps in pkg.split(',') for p in ps.strip().split()]
      for p in pkg:
        if p in PKG:
          pkgs.append(p)
          print(f'# use {p}', file=sys.stderr)
        elif p in KEYWORDS:
          pkgs.append(KEYWORDS[p])
          print(f'# use {KEYWORDS[p]}', file=sys.stderr)
        else:
          suggest = difflib.get_close_matches(p, list(PKG) + list(KEYWORDS))
          if suggest:
            print('# Did you mean', ' or '.join(suggest), '?', file=sys.stderr)
          else:
            print(f'# Invalid Package Name `{p}`', file=sys.stderr)
    except EOFError:
      print('', file=sys.stderr)
      break
  return pkgs


def list_packages(count):
  pkgs = {pkg: ', '.join(PKG[pkg].get('__keywords', '')) for pkg in PKG}
  pkgs = {k: f'({v})' if v else '' for k, v in pkgs.items()}
  if count == 1:
    print('\n'.join([f'{k} {v}' for k, v in pkgs.items()]))
  else:
    print(' '.join(PKG.keys()))


def preprocess_meta():
  for pkg in PKG:
    if '__meta' in PKG[pkg]:
      meta = PKG[pkg]['__meta']
      PKG[pkg].update(META_PKG[meta])
      PKG[pkg].pop('__meta')


def valid_use(pkg):
  if pkg in PKG:
    return pkg
  if pkg in KEYWORDS:
    return KEYWORDS[pkg]
  raise argparse.ArgumentTypeError(f'Invalid Package Name `{pkg}`')


if __name__ == '__main__':
  preprocess_meta()
  current_shell = os.path.basename(env.get('SHELL', 'bash'))
  parser = argparse.ArgumentParser(
      description='Simple Environment Variable Management')
  parser.add_argument(
      '-s',
      '--shell',
      default=current_shell,
      type=str,
      help='syntax (default: current shell `%(default)s`)')
  parser.add_argument(
      '-u', '--use', action='append', type=valid_use, metavar='PACKAGE')
  parser.add_argument(
      '-ne',
      '--not-expand',
      action='store_true',
      help='[ne] environment vairable')
  parser.add_argument(
      '-i',
      '--interactive',
      action='store_true',
      help='choose packages [interactively]')
  # parser.add_argument('-o', '--output', type=str, metavar='FILENAME')
  parser.add_argument(
      '-l', '--list', action='count', help='available packages')
  args = parser.parse_args()
  if args.interactive:
    pkgs = interactive_mode()
    main(args.shell, pkgs, not args.not_expand)
  elif args.use:
    main(args.shell, args.use, not args.not_expand)
  elif args.list:
    list_packages(args.list)
