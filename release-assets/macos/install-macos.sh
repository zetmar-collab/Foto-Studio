#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Brak Python 3. Zainstaluj Python 3.10 lub nowszy z https://www.python.org/downloads/macos/"
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

".venv/bin/python" -m pip install -r requirements.txt
chmod +x Uruchom-Foto-Studio.command Utworz-skrot-na-pulpicie-macOS.command

echo "Foto-Studio jest gotowe. Uruchom: ./Uruchom-Foto-Studio.command"
