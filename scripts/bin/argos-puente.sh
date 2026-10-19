#!/bin/bash
# Copia la carpeta <CARPETA_DRIVE> de Drive a ArgOS (solo agrega/actualiza, nunca borra)
SRC="<REMOTO_RCLONE>:<CARPETA_DRIVE>"
DST="/opt/argos-data/puente"
STATUS=/var/lib/argos/puente-status
LOG=/var/log/argos-puente.log
mkdir -p "$DST" /var/lib/argos
exec 9>/run/argos-puente.lock
flock -n 9 || { echo "$(date -Is) skip: ya corriendo" >> "$LOG"; exit 0; }
if rclone copy "$SRC" "$DST" --create-empty-src-dirs --drive-export-formats docx,xlsx,pptx,pdf --log-file "$LOG" --log-level NOTICE --stats-one-line --stats 0; then
  echo "OK $(date -Is)" > "$STATUS"
else
  echo "FAIL $(date -Is)" > "$STATUS"; exit 1
fi
