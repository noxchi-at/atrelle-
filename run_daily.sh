#!/usr/bin/env bash
#
# Aufgabe 6 - taeglicher Lauf der Atrelle Fit-Pipeline.
# Schreibt die Fits in einen Ordner mit Datumsstempel: fits/JJJJ-MM-TT/
#
# Konfiguration ueber Umgebungsvariablen (optional):
#   COUNT   Anzahl Fits pro Tag   (Default 7)
#   TRYON   "1" -> zusaetzlich prompt_tryon.txt
#
# Manuell testen:   ./run_daily.sh
# Taeglich per cron: siehe README (Abschnitt "Taeglich automatisch").

set -euo pipefail

# immer im Projektordner arbeiten, egal von wo cron startet
cd "$(dirname "$(readlink -f "$0")")"

COUNT="${COUNT:-7}"
DATE="$(date +%F)"
OUT="fits/${DATE}"
LOG="logs/${DATE}.log"
PY="$(command -v python3 || command -v python)"

mkdir -p logs

{
  echo "=== Atrelle Fit-Run ${DATE} $(date +%T) ==="
  # Uhren-/Parfuembilder sicherstellen (idempotent)
  "$PY" fetch_assets.py

  ARGS=(--count "$COUNT" --out "$OUT")
  [ "${TRYON:-0}" = "1" ] && ARGS+=(--tryon)

  "$PY" generate_fits.py "${ARGS[@]}"
  echo "=== fertig: $OUT ==="
} >> "$LOG" 2>&1

echo "Fertig. Fits in ${OUT}, Log in ${LOG}"
