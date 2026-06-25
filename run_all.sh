#!/usr/bin/env bash
#
# Reproduce everything end to end with a classic, system Python (no virtualenv):
# install dependencies, then run the two stages in order (collect -> figures).
#
#   bash run_all.sh
#
# Uses `python3` by default; override with PYTHON=python3.13 (or a full path).
# The pip line installs into that interpreter's site-packages. If your default
# python3 is a Homebrew / "externally-managed" build, pip may refuse: either
# point PYTHON at the python.org interpreter, or add --user to the pip command.
# Already have the packages? Comment out the install line.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
cd "$PROJECT_DIR"

echo ">> installing requirements for $("$PYTHON" --version 2>&1)"
"$PYTHON" -m pip install -r requirements.txt

echo ">> [1/2] collecting data"
"$PYTHON" 01_collect_data.py
echo ">> [2/2] making figures"
"$PYTHON" 02_make_figures.py

echo ">> done. See ./figures and ./data"
