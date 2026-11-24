#!/bin/bash
# Doppelklick: startet den NMS-Tracker und öffnet ihn im Browser.
# Beenden: Ctrl+C in diesem Fenster, oder das Fenster schließen, oder stop.command.
cd "$(dirname "$0")" || exit 1
URL="http://127.0.0.1:5050"

if lsof -ti tcp:5050 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Server läuft schon. Öffne $URL"
  open "$URL"
  exit 0
fi

if [ ! -x .venv/bin/python ]; then
  echo "Einrichtung (einmalig) ..."
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt || exit 1
fi

(sleep 1.5; open "$URL") &
echo "NMS-Tracker läuft auf $URL"
echo "Zum Beenden: Ctrl+C oder dieses Fenster schließen."
exec .venv/bin/python app.py
