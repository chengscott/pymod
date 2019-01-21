import os
import sys


class ShellError(Exception):
  pass


class ShellNotSupported(ShellError):
  pass


class PackageError(Exception):
  pass


class PackageNotFound(PackageError):
  pass


class Manager:
  """Environment Variable Manager"""

  def __init__(self, package={}):
    """Initialize from a dict"""
    self.__home_path = os.environ.get('HOME', '')
    self.__package = package
    # {keyword: package}
    self.__keyword = {
        key: pkg
        for pkg in package for key in package[pkg].get('__keywords', {})
    }
    self.__keyword.update({pkg: pkg for pkg in package})
    # {package: keyword format str}
    pkg_kwd = {
        pkg: ', '.join(self.__package[pkg].get('__keywords', ''))
        for pkg in self.__package
    }
    self.__pkg_kwd = {
        pkg: f'({kwd})' if kwd else ''
        for pkg, kwd in pkg_kwd.items()
    }
    self.shell = os.path.basename(os.environ.get('SHELL', 'bash'))
    self.use_shell(self.shell)

  @classmethod
  def from_json(cls,
                pkg='pkg.json',
                meta='meta.json',
                search_path=('/usr/local/etc/pymod', '~/.config/pymod', '')):
    """Initialize from json files under search path"""
    pkg = cls.__load_json(pkg, search_path)
    if meta:
      meta = cls.__load_json(meta, search_path)
      cls.__preprocess_meta(pkg, meta)
    return cls(pkg)

  @classmethod
  def from_ini(cls,
               pkg='pkg.ini',
               meta='meta.ini',
               search_path=('/usr/local/etc/pymod', '~/.config/pymod', '')):
    """Initialize from ini files under search_path"""
    pkg = cls.__load_ini(pkg, search_path)
    if meta:
      meta = cls.__load_ini(meta, search_path, is_meta=True)
      cls.__preprocess_meta(pkg, meta)
    return cls(pkg)

  @staticmethod
  def __load_json(config, search_path):
    import json
    ret = {}
    for path in search_path:
      try:
        filename = os.path.join(os.path.expanduser(path), config)
        with open(filename) as f:
          ret.update(json.load(f))
      except FileNotFoundError:
        pass
    return ret

  @staticmethod
  def __load_ini(config, search_path, is_meta=False):
    import configparser
    import re
    RE = re.compile(r'^\[(.*)\]', flags=re.MULTILINE)

    def load_pkg(res):
      ret = {}
      res = iter(RE.split(res)[1:])
      for meta in res:
        pkg = next(res)
        conf = configparser.ConfigParser()
        conf.optionxform = str
        conf.read_string(pkg)
        for k, v in conf.items():
          if k != 'DEFAULT':
            pkg = dict(v)
            pkg['__keywords'] = re.split('[ ,]+', pkg.pop('alias', ''))
            pkg['__prefix'] = pkg.pop('prefix', '')
            pkg['__cmd'] = pkg.pop('cmd', '')
            pkg['__meta'] = meta
            ret[k] = {
                pk: pv if pk.startswith('__') else re.split('[ :,]+', pv)
                for pk, pv in pkg.items()
            }
      return ret

    def load_meta(res):
      ret = {}
      conf = configparser.ConfigParser()
      conf.optionxform = str
      conf.read_string(res)
      ret = {k: dict(v) for k, v in conf.items() if k != 'DEFAULT'}
      for k, v in conf.items():
        if k != 'DEFAULT':
          pkg = dict(v)
          pkg['__keywords'] = re.split('[ ,]+', pkg.pop('alias', ''))
          pkg['__cmd'] = pkg.pop('cmd', '')
          ret[k] = {
              pk: pv if pk.startswith('__') else re.split('[ :,]+', pv)
              for pk, pv in pkg.items()
          }
      return ret

    ret = {}
    for path in search_path:
      try:
        filename = os.path.join(os.path.expanduser(path), config)
        with open(filename) as f:
          res = f.read()
          if is_meta:
            res = load_meta(res)
          else:
            res = load_pkg(res)
        ret.update(res)
      except FileNotFoundError:
        pass
    return ret

  @staticmethod
  def __preprocess_meta(pkg, meta):
    mk = {}
    for v in meta.values():
      ks = v.pop('__keywords', '')
      mk.update({k: v for k in ks})
    meta.update(mk)
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
        self.__output(f'export {var}={new_val}')

    def use_fish(evars):
      for var, val, old_val in evars:
        if var == 'PATH':
          new_val = ' '.join(val.split(':') + old_val.split(':'))
        else:
          new_val = ':'.join(filter(None, [val, old_val]))
        self.__output(f'set -x {var} {new_val};')

    def use_csh(evars):
      raise NotImplementedError

    use = {
        'bash': use_bash,
        'zsh': use_bash,
        'fish': use_fish,
        'csh': use_csh,
        'tcsh': use_csh,
    }
    if shell in use:
      self._shell = use[shell]
    else:
      raise ShellNotSupported(f'`{shell}` is not supported')

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
      cmd = path['__cmd']
      if isinstance(cmd, list):
        for c in cmd:
          self.__output(c)
      else:
        self.__output(cmd)
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
        raise PackageNotFound(f'package `{p}` is not found')
    self.__use_package(pkgs, *args, **kwds)

  def find(self, pkg=''):
    """Search for a package name interactively"""
    import difflib
    if not pkg:
      pkg = input('Package name: ')
    keyword = list(self.__keyword)
    if pkg in keyword:
      pkg = self.__keyword[pkg]
      kwd = self.__pkg_kwd[pkg]
      self.__output(f'Avaiable Package `{pkg}` {kwd}', interactive=True)
    else:
      suggest = difflib.get_close_matches(pkg, keyword)
      if len(suggest) == 1:
        pkg, = suggest
        pkg = self.__keyword[pkg]
        kwd = self.__pkg_kwd[pkg]
        self.__output(f'Did you mean `{pkg}` {kwd} ?')
      elif suggest:
        pkgs = ' or '.join(suggest)
        self.__output(f'Did you mean {pkgs} ?', interactive=True)
      else:
        raise PackageNotFound(f'package `{pkg}` is not found')

  def show(self, name=''):
    """Show available packages"""
    if name:
      self.find(name)
    else:
      for pkg, kwd in self.__pkg_kwd.items():
        self.__output(pkg, kwd)

  def __output(self, *line, interactive=False):
    if interactive:
      print(*line, file=sys.stderr)
    else:
      print(*line)
