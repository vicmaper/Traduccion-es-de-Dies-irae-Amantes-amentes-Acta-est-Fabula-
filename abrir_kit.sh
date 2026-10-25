#!/bin/sh
# Linux / Steam Deck (modo escritorio). Sin argumentos abre la ventana; si falta tkinter usa la consola:
#   ./abrir_kit.sh instalar "/home/deck/.local/share/Steam/steamapps/common/Dies irae ~Amantes amentes~"
cd "$(dirname "$0")/kit" || exit 1
if [ $# -eq 0 ] && ! python3 -c "import tkinter" 2>/dev/null; then
  echo "No hay tkinter: usa la consola, por ejemplo:"
  echo "  ./abrir_kit.sh instalar \"$HOME/.local/share/Steam/steamapps/common/Dies irae ~Amantes amentes~\""
  exit 1
fi
exec python3 di_kit.py "$@"
