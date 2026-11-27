#!/bin/bash
# Double-click to start LexiCount on a Mac.
cd "$(dirname "$0")" || exit 1
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then
    PY="$candidate"; break
  fi
done
if [ -z "$PY" ]; then
  echo
  echo "  LexiCount needs Python 3.10 or newer, which was not found on this Mac."
  echo
  echo "  1. Download Python from https://www.python.org/downloads/"
  echo "  2. Double-click START_LexiCount_Mac.command again."
  echo
else
  "$PY" launch.py "$@"
fi
echo
read -n 1 -s -r -p "Press any key to close this window."
