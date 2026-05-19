#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

DESKTOP="$HOME/Desktop"
if [ ! -d "$DESKTOP" ]; then
  DESKTOP="$HOME/Pulpit"
fi
mkdir -p "$DESKTOP"

TARGET="$PWD/Uruchom-Foto-Studio.command"
SHORTCUT="$DESKTOP/Uruchom Foto-Studio.command"

cat > "$SHORTCUT" <<EOF
#!/usr/bin/env bash
cd "$PWD"
exec "$TARGET"
EOF

chmod +x "$SHORTCUT"
echo "Utworzono skrot: $SHORTCUT"
