#!/bin/bash
# 로컬 자동 업로드는 비활성화되었습니다.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="/tmp/essay-shorts-retry.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "Local retry is disabled. GitHub Actions is the only automatic uploader."
exit 0
