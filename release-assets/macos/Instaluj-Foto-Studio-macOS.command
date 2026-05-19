#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

chmod +x install-macos.sh Uruchom-Foto-Studio.command Utworz-skrot-na-pulpicie-macOS.command
./install-macos.sh
./Utworz-skrot-na-pulpicie-macOS.command

echo "Uruchamiam Foto-Studio..."
./Uruchom-Foto-Studio.command
