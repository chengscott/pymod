#!/usr/bin/fish
set PYMOD_CMD (command -v pymod)
function pymod
  if [ (count $argv) -gt 0 ]; and [ $argv[1] = "use" ]; eval (eval $PYMOD_CMD $argv);
  else; eval $PYMOD_CMD $argv; end
end
