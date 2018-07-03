#!/usr/bin/env python3.6
"""Simple Environment Variable Management
"""
import argparse
import difflib
import json
import os
from os import environ as env
import sys

HOME_PATH = env.get('HOME', '')
META_PKG, PKG = {}, {}
with open('meta.json') as f:
  META_PKG = json.load(f)
with open('pkg.json') as f:
  PKG = json.load(f)
KEYWORDS = dict(
    [(key, pkg) for pkg in PKG for key in PKG[pkg].get('__keywords', {})])
for pkg in PKG:
  if '__meta' in PKG[pkg]:
    meta = PKG[pkg]['__meta']
    PKG[pkg].update(META_PKG[meta])
    PKG[pkg].pop('__meta')


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


def valid_use(pkg):
  if pkg in PKG:
    return pkg
  if pkg in KEYWORDS:
    return KEYWORDS[pkg]
  raise argparse.ArgumentTypeError(f'Invalid Module Name `{pkg}`')


if __name__ == '__main__':
  current_shell = os.path.basename(env.get('SHELL', 'bash'))
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-s',
      '--shell',
      help='(default: current shell `%(default)s`)',
      default=current_shell,
      type=str)
  parser.add_argument('-u', '--use', action='append', type=valid_use)
  parser.add_argument('-ne', '--not-expand', action='store_true')
  parser.add_argument('-i', '--interactive', action='store_true')
  args = parser.parse_args()
  if args.interactive:
    pkgs = []
    while True:
      try:
        pkg = input()
        pkg = [p for ps in pkg.split(',') for p in ps.strip().split()]
        for p in pkg:
          if p in PKG:
            pkgs.append(p)
            print(f'# use {p}')
          elif p in KEYWORDS:
            pkgs.append(KEYWORDS[p])
            print(f'# use {KEYWORDS[p]}')
          else:
            suggest = difflib.get_close_matches(p, list(PKG) + list(KEYWORDS))
            print('# Did you mean', ' or '.join(suggest), '?')
      except EOFError:
        break
    main(args.shell, pkgs, not args.not_expand)
  elif args.use:
    main(args.shell, args.use, not args.not_expand)
