#!/bin/bash
# tube-autopilot setup wizard launcher (macOS / Linux)
cd "$(dirname "$0")"
echo
echo "  tube-autopilot SETUP WIZARD"
echo "  ---------------------------"
echo "  If nothing happens, install Python 3 from https://www.python.org/"
echo "  then double-click this file again."
echo
if command -v python3 >/dev/null 2>&1; then
  python3 tools/setup_wizard.py
elif command -v python >/dev/null 2>&1; then
  python tools/setup_wizard.py
else
  echo "  Python was not found. Install it from https://www.python.org/"
fi
echo ""
read -r -p "Press ENTER to close this window..."
