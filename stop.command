#!/bin/bash
# Doppelklick: beendet den NMS-Tracker.
PID=$(lsof -ti tcp:5050 -sTCP:LISTEN)
if [ -z "$PID" ]; then
  echo "Server läuft nicht."
else
  kill $PID && echo "Server beendet."
fi
sleep 1
