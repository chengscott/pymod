import difflib
import sys


def interactive_mode(keywords):
  def prompt(msg, *args, **kwds):
    print(msg, *args, **kwds, file=sys.stderr)

  pkgs = []
  prompt(f'# Input packages until EOF')
  while True:
    prompt('> ', end='')
    try:
      pkg = input()
      pkg = [p for ps in pkg.split(',') for p in ps.strip().split()]
      for p in pkg:
        if p in keywords:
          pkgs.append(keywords[p])
          prompt(f'# use {keywords[p]}')
        else:
          suggest = difflib.get_close_matches(p, list(keywords))
          if suggest:
            prompt('# Did you mean', ' or '.join(suggest), '?')
          else:
            prompt(f'# Invalid Package Name `{p}`')
    except EOFError:
      prompt('')
      break
  return pkgs
