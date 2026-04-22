#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/kimgwonil/youtube-shorts-automation"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/catch-up-upload.log"

mkdir -p "$LOG_DIR"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S %Z'
}

log() {
  echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

cd "$PROJECT_DIR"

# Give the startup sync agent a brief window to finish fetch/pull first.
sleep 20

if [[ ! -d ".venv" ]]; then
  log ".venv not found. Skipping catch-up upload."
  exit 0
fi

source .venv/bin/activate

TODAY="$(TZ=Asia/Seoul date '+%Y-%m-%d')"
CURRENT_HOUR_MINUTE="$(TZ=Asia/Seoul date '+%H%M')"

if [[ "$CURRENT_HOUR_MINUTE" -lt "0700" ]]; then
  log "Current time is before 07:00 KST. Catch-up upload skipped."
  exit 0
fi

if python - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

state_file = Path("data/state.json")
today = Path("/dev/stdin").read_text().strip()

if not state_file.exists():
    raise SystemExit(1)

state = json.loads(state_file.read_text(encoding="utf-8"))
raise SystemExit(0 if today in state.get("recent_dates", []) else 1)
PY
<<<"$TODAY"; then
  log "Today's upload is already recorded in state.json. Catch-up upload skipped."
  exit 0
fi

log "Today's upload is missing after 07:00 KST. Starting catch-up upload."
python scripts/run_daily.py >>"$LOG_FILE" 2>&1
log "Catch-up upload finished."
