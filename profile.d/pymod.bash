#!/bin/bash
PYMOD_CMD=$(command -v pymod)
pymod() { if [ "$1" = "use" ]; then $($PYMOD_CMD "$@"); else $PYMOD_CMD "$@"; fi }
