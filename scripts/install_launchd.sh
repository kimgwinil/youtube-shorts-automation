#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/kimgwonil/youtube-shorts-automation"
USER_DOMAIN="gui/$(id -u)"
PLIST_NAMES=(
  "com.kimgwonil.youtube-shorts-daily.plist"
  "com.kimgwonil.youtube-shorts-sync.plist"
  "com.kimgwonil.youtube-shorts-catchup.plist"
)

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$PROJECT_DIR/logs"
chmod +x "$PROJECT_DIR/scripts/sync_repo_on_boot.sh"
chmod +x "$PROJECT_DIR/scripts/catch_up_upload_on_boot.sh"

BOOTSTRAP_FAILED=0

for PLIST_NAME in "${PLIST_NAMES[@]}"; do
  SOURCE_PLIST="$PROJECT_DIR/launchd/$PLIST_NAME"
  TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"
  cp "$SOURCE_PLIST" "$TARGET_PLIST"
  launchctl bootout "$USER_DOMAIN" "$TARGET_PLIST" >/dev/null 2>&1 || true
  if launchctl bootstrap "$USER_DOMAIN" "$TARGET_PLIST"; then
    echo "installed: $TARGET_PLIST"
  else
    BOOTSTRAP_FAILED=1
    echo "copied but not loaded: $TARGET_PLIST"
  fi
done

if [[ "$BOOTSTRAP_FAILED" -eq 1 ]]; then
  echo "launchctl bootstrap failed in this session."
  echo "Run this from your logged-in Mac terminal:"
  echo "launchctl bootstrap $USER_DOMAIN $HOME/Library/LaunchAgents/com.kimgwonil.youtube-shorts-sync.plist"
  echo "launchctl bootstrap $USER_DOMAIN $HOME/Library/LaunchAgents/com.kimgwonil.youtube-shorts-catchup.plist"
  echo "launchctl bootstrap $USER_DOMAIN $HOME/Library/LaunchAgents/com.kimgwonil.youtube-shorts-daily.plist"
else
  echo "start sync now: launchctl start com.kimgwonil.youtube-shorts-sync"
  echo "start catch-up now: launchctl start com.kimgwonil.youtube-shorts-catchup"
  echo "start daily job now: launchctl start com.kimgwonil.youtube-shorts-daily"
fi
