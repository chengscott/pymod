#!/usr/bin/env python3.6
"""Simple Environment Variable Management
"""
import argparse
import os
import sys

MOD = {
    'cuda-9.2': {
        '__keywords': ['cuda', 'cuda9.2'],
        'PATH': '/usr/local/cuda-9.2/bin',
        'LD_LIBRARY_PATH': '/usr/local/cuda-9.2/lib'
    },
    'nccl-cuda9.2': {
        '__keywords': ['nccl', 'nccl-2.2.12+cuda-9.2'],
        'LD_LIBRARY_PATH': '{HOME}/nccl/lib'
    },
    'ompi-1.10': {
        '__keywords': ['openmpi-1.10.7', 'ompi1', 'ompi-1', 'ompi-1.10.7'],
        'PATH': '{HOME}/ompi1/bin',
        'LD_LIBRARY_PATH': '{HOME}/ompi1/lib'
    },
    'ompi-3': {
        '__keywords': ['openmpi-3.1.0', 'ompi3', 'ompi', 'openmpi'],
        'PATH': '{HOME}/ompi3/bin',
        'LD_LIBRARY_PATH': '{HOME}/ompi3/lib'
    },
}
KEYWORDS = dict(
    [(key, mod) for mod in MOD for key in MOD[mod].get('__keywords', {})])
env = os.environ


def use_fish(var, val, expand):
  old_val = ''
  if expand:
    old_val = env.get(var, '').replace(':', ' ')
    val = val.format(HOME=env.get('HOME', '/usr'))
  else:
    old_val = f'${var}'
    val = val.format(HOME='$HOME')
  print(f'set -x {var} {val} {old_val}')


def use_bash(var, val, expand):
  old_val = ''
  if expand:
    old_val = env.get(var, '')
    val = val.format(HOME=env.get('HOME', '/usr'))
  else:
    old_val = f'${var}'
    val = val.format(HOME='$HOME')
  print(f'export {var}={val}:{old_val}')


USE_SHELL = {
    'bash': use_bash,
    'fish': use_fish,
}


def main(shell, mods, expand):
  if shell not in use_shell:
    print(f'`{shell}` is not a supported shell', file=sys.stderr)
  use_shell = USE_SHELL[shell]
  for mod in mods:
    for var, val in MOD[mod].items():
      if not var.startswith('__'):
        use_shell(var, val, expand=expand)


def valid_use(mod):
  if mod in MOD:
    return mod
  if mod in KEYWORDS:
    return KEYWORDS[mod]
  raise argparse.ArgumentTypeError('Invalid Module Name')


if __name__ == '__main__':
  current_shell = os.path.basename(env.get('SHELL', 'bash'))
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--shell', default=current_shell, type=str)
  parser.add_argument('-u', '--use', action='append', type=valid_use)
  parser.add_argument('-ne', '--not-expand', action='store_true')
  args = parser.parse_args()
  if args.use:
    main(args.shell, args.use, not args.not_expand)
