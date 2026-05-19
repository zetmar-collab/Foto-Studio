#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

".venv/bin/python" -m pip install -r requirements.txt
export FOTO_STUDIO_NO_BROWSER=1
open http://localhost:3000 >/dev/null 2>&1 || true
".venv/bin/python" app.py
