#!/bin/bash
# Doppelklick: sichert alle Daten in einen neuen Ordner unter export/ und zeigt ihn im Finder.
# Funktioniert auch bei laufendem Server.
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then echo "Bitte zuerst start.command einmal ausführen (Einrichtung)."; sleep 4; exit 1; fi
OUT=$(.venv/bin/python exporter.py) || { echo "$OUT"; echo "Export fehlgeschlagen."; sleep 6; exit 1; }
echo "$OUT"
ORDNER=$(echo "$OUT" | sed -n 's/^Export fertig: //p')
[ -n "$ORDNER" ] && open "$ORDNER"
sleep 2
