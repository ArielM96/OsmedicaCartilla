#!/usr/bin/env bash
# Sincroniza datasets desde osmedica.com.ar y reinicia la API para recargar JSON.
set -euo pipefail

ROOT="/opt/dash/OsmedicaCartilla"
LOG_DIR="/var/log/osmedica-cartilla"
LOG_FILE="${LOG_DIR}/sync.log"
LOCK="/tmp/osmedica_cartilla_sync.lock"

mkdir -p "$LOG_DIR"

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "$(date -Is) sync omitido: otra corrida en curso" >>"$LOG_FILE"
  exit 0
fi

{
  echo "===== $(date -Is) sync iniciado ====="
  cd "$ROOT"
  "$ROOT/.venv/bin/pip" install -q -r requirements-sync.txt
  "$ROOT/.venv/bin/python" research/discover.py
  systemctl restart osmedica-cartilla.service

  health_ok=0
  for attempt in 1 2 3 4 5; do
    sleep 2
    if curl -fsS --connect-timeout 5 "http://127.0.0.1:8012/api/v1/health" >/dev/null; then
      health_ok=1
      break
    fi
    echo "$(date -Is) health check intento ${attempt}/5 falló, reintentando..." >&2
  done

  if [[ "$health_ok" -eq 1 ]]; then
    echo "$(date -Is) sync OK — API health 200"
  else
    echo "$(date -Is) sync ERROR — health check falló tras reinicio" >&2
    exit 1
  fi
} >>"$LOG_FILE" 2>&1
