#!/usr/bin/env python3.6
"""Simple Environment Variable Management
"""
import argparse
import os
from os import environ as env

META_PKG = {
    'gcc': {
        'CPATH': '{PREFIX}/include',
        'LD_LIBRARY_PATH':
        ['{PREFIX}/lib', '{PREFIX}/lib64', '{PREFIX}/libexec'],
        'LIBRARY_PATH': ['{PREFIX}/lib', '{PREFIX}/lib64', '{PREFIX}/libexec'],
        'PATH': '{PREFIX}/bin',
    },
    'intel': {
        '__cmd': 'source {PREFIX}/bin/compilervars.sh intel64',
    },
    'standard': {
        'CPATH': '{PREFIX}/include',
        'LD_LIBRARY_PATH': '{PREFIX}/lib',
        'LIBRARY_PATH': '{PREFIX}/lib',
        'PATH': '{PREFIX}/bin',
    },
    'standard-64': {
        'CPATH': '{PREFIX}/include',
        'LD_LIBRARY_PATH': '{PREFIX}/lib64',
        'LIBRARY_PATH': '{PREFIX}/lib64',
        'PATH': '{PREFIX}/bin',
    }
}
PKG = {
    'gcc-8.1.0': {
        '__keywords': ['gcc'],
        '__prefix': '/home/chengscott/.local/gcc-8.1.0',
        '__meta': 'gcc',
    },
    'cuda-9.2': {
        '__keywords': ['cuda'],
        '__prefix': '/usr/local/cuda-9.2',
        '__meta': 'standard-64',
        'CUDA_HOME': '{PREFIX}',
    },
    'cudnn-7.1+cuda-9.2': {
        '__keywords': ['cudnn', 'cudnn-7.1'],
        '__prefix': '{HOME}/.local/cudnn-9.2',
        'CPATH': '{PREFIX}/include',
        'LD_LIBRARY_PATH': '{PREFIX}/lib64',
        'LIBRARY_PATH': '{PREFIX}/lib64',
    },
    'nccl-2.12+cuda-9.2': {
        '__keywords': ['nccl', 'nccl-2.2'],
        '__prefix': '{HOME}/.local/nccl_2.2.12-1+cuda9.2',
        'CPATH': '{PREFIX}/include',
        'LD_LIBRARY_PATH': '{PREFIX}/lib',
        'LIBRARY_PATH': '{PREFIX}/lib',
    },
    'jdk-1.8': {
        '__prefix': '{HOME}/.local/jdk1.8.0_171',
        '__meta': 'standard',
        'JAVA_HOME': '{PREFIX}',
    },
    'openmpi-1': {
        '__keywords': ['openmpi-1.10.7', 'ompi-1', 'ompi-1.10.7'],
        '__prefix': '{HOME}/ompi1',
        '__meta': 'standard',
    },
    'openmpi-3': {
        '__keywords':
        ['openmpi-3.1.0', 'ompi-3', 'ompi-3.1.0', 'ompi', 'openmpi'],
        '__prefix':
        '{HOME}/ompi3',
        '__meta':
        'standard',
    },
    'intel-2018': {
        '__keywords': ['intel'],
        '__prefix': '/opt/intel2018',
        '__meta': 'intel'
    },
    'intel-2017': {
        '__prefix': '/opt/intel2017',
        '__meta': 'intel'
    },
}
KEYWORDS = dict(
    [(key, pkg) for pkg in PKG for key in PKG[pkg].get('__keywords', {})])
HOME_PATH = env.get('HOME', '')
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
    import sys
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
  raise argparse.ArgumentTypeError('Invalid Module Name')


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
  # parser.add_argument('-c', '--confirm', action='store_true')
  args = parser.parse_args()
  if args.use:
    main(args.shell, args.use, not args.not_expand)
