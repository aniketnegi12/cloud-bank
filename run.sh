#!/usr/bin/env bash
set -e
# Create and install venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip setuptools wheel
  .venv/bin/pip install -r requirements.txt
fi

# Activate venv and run
. .venv/bin/activate
python main.py
