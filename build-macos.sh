#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi
".venv/bin/python" -m pip install -r requirements.txt -r requirements-build.txt
".venv/bin/pyinstaller" --noconfirm --name Foto-Studio --add-data "index.html:." --add-data "manifest.json:." --add-data "sw.js:." --add-data "icons:icons" app.py
echo "Gotowe: dist/Foto-Studio/Foto-Studio"
