#!/bin/bash
set -o pipefail
. /etc/argos/restic.env
LOG=/var/log/argos-backup.log
STATUS=/var/lib/argos/backup-status
mkdir -p /var/lib/argos
log(){ echo "[$(date '+%F %T %Z')] $*" >> "$LOG"; }
fail(){ log "FAIL: $1"; echo "FAIL $(date -Iseconds) $1" > "$STATUS"; exit 1; }
exec >>"$LOG" 2>&1
log "=== Inicio respaldo ==="
restic backup /etc /home/<USUARIO> /opt /var/lib/docker/volumes \
  --exclude-caches --exclude '/home/<USUARIO>/.cache' --exclude '**/.cache' \
  --tag argos --host "$RESTIC_HOST" || fail "backup"
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune --host "$RESTIC_HOST" || fail "forget/prune"
WEEK=$(date +%G-%V); LAST=$(cat /var/lib/argos/last-check-week 2>/dev/null)
if [ "$WEEK" != "$LAST" ]; then
  restic check || fail "check"
  echo "$WEEK" > /var/lib/argos/last-check-week
fi
echo "OK $(date -Iseconds)" > "$STATUS"
log "=== OK ==="
