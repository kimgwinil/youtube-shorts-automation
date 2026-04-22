#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/kimgwonil/youtube-shorts-automation"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/repo-sync.log"

mkdir -p "$LOG_DIR"

timestamp() {
  date '+%Y-%m-%d %H:%M:%S %Z'
}

log() {
  echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

cd "$PROJECT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  log "Not a git repository: $PROJECT_DIR"
  exit 1
fi

CURRENT_BRANCH="$(git branch --show-current)"
if [[ -z "$CURRENT_BRANCH" ]]; then
  log "Detached HEAD detected. Skipping automatic sync."
  exit 0
fi

log "Starting startup sync on branch $CURRENT_BRANCH"
git fetch origin "$CURRENT_BRANCH" >>"$LOG_FILE" 2>&1

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "origin/$CURRENT_BRANCH")"
BASE_SHA="$(git merge-base HEAD "origin/$CURRENT_BRANCH")"

if [[ -n "$(git status --porcelain)" ]]; then
  log "Working tree has local changes. Fetched remote only; merge skipped."
  exit 0
fi

if [[ "$LOCAL_SHA" == "$REMOTE_SHA" ]]; then
  log "Repository already up to date."
  exit 0
fi

if [[ "$LOCAL_SHA" == "$BASE_SHA" ]]; then
  git pull --ff-only origin "$CURRENT_BRANCH" >>"$LOG_FILE" 2>&1
  log "Fast-forward sync completed."
  exit 0
fi

if [[ "$REMOTE_SHA" == "$BASE_SHA" ]]; then
  log "Local branch is ahead of origin. Automatic push skipped."
  exit 0
fi

log "Local and remote branches diverged. Manual sync required."
exit 0
