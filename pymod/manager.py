import json
import os


class Manager:
  """Environment Variable Manager"""

  def __init__(self, package={}):
    """Initialize from a dict"""
    self.__home_path = os.environ.get('HOME', '')
    self.__package = package
    self.__keyword = {
        key: pkg
        for pkg in package for key in package[pkg].get('__keywords', {})
    }
    self.__keyword.update({pkg: pkg for pkg in package})
    self.shell = os.path.basename(os.environ.get('SHELL', 'bash'))
    self.use_shell(self.shell)

  @classmethod
  def from_json(cls,
                pkg='pkg.json',
                meta='meta.json',
                search_path=('/usr/local/etc/pymod', '~/.config/pymod', '')):
    """Initialize from jsons under these search path"""
    pkg = cls.__load_json(pkg, search_path)
    if meta:
      meta = cls.__load_json(meta, search_path)
      cls.__preprocess_meta(pkg, meta)
    return cls(pkg)

  def __load_json(config, search_path):
    ret = {}
    for path in search_path:
      try:
        filename = os.path.join(os.path.expanduser(path), config)
        with open(filename) as f:
          ret.update(json.load(f))
      except FileNotFoundError:
        pass
    return ret

  def __preprocess_meta(pkg, meta):
    for p in pkg:
      if '__meta' in pkg[p]:
        m = pkg[p]['__meta']
        pkg[p].update(meta[m])
        pkg[p].pop('__meta')

  def use_shell(self, shell):
    """Use a shell syntax"""

    def use_bash(evars):
      for var, val, old_val in evars:
        new_val = ':'.join(filter(None, [val, old_val]))
        print(f'export {var}={new_val}')

    def use_fish(evars):
      for var, val, old_val in evars:
        if var == 'PATH':
          new_val = ' '.join(val.split(':') + old_val.split(':'))
        else:
          new_val = ':'.join(filter(None, [val, old_val]))
        print(f'set -x {var} {new_val};')

    use = {
        'bash': use_bash,
        'fish': use_fish,
        'zsh': use_bash,
    }
    if shell not in use:
      print(f'`{shell}` is not a supported shell')
    else:
      self._shell = use[shell]

  def __use_package(self, pkgs, expand=False):
    from collections import defaultdict
    path = defaultdict(list)
    for pkg in pkgs:
      prefix = self.__package[pkg].get('__prefix', '')
      for var, val in self.__package[pkg].items():
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
      evars = [(var, val.format(HOME=self.__home_path), os.environ.get(
          var, '')) for var, val in evars]
    else:
      evars = [(var, val.format(HOME='$HOME'), f'${var}')
               for var, val in evars]
    self._shell(evars)

  def use(self, pkgs, *args, **kwds):
    """Use a (list of) package"""
    if not isinstance(pkgs, list):
      pkgs = [pkgs]
    for i, p in enumerate(pkgs):
      if p in self.__package:
        continue
      elif p in self.__keyword:
        pkgs[i] = self.__keyword[p]
      else:
        print(f'# Invalid Package Name `{p}`')
        return
    self.__use_package(pkgs, *args, **kwds)

  def find(self):
    """Search for a package name interactively"""
    import difflib
    import sys

    def prompt(msg, *args, **kwds):
      print(msg, *args, **kwds, file=sys.stderr)

    pkg = input()
    keyword = list(self.__keyword)
    if pkg in keyword:
      prompt(f'# Avaiable Package `{self.__keyword[pkg]}`')
    else:
      suggest = difflib.get_close_matches(pkg, keyword)
      if suggest:
        prompt('# Did you mean', ' or '.join(suggest), '?')
      else:
        prompt(f'# Invalid Package Name `{p}`')

  def show(self, avail):
    """Show available packages"""
    pkgs = {
        pkg: ', '.join(self.__package[pkg].get('__keywords', ''))
        for pkg in self.__package
    }
    pkgs = {k: f'({v})' if v else '' for k, v in pkgs.items()}
    print('\n'.join([f'{k} {v}' for k, v in pkgs.items()]))
