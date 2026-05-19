#!/bin/bash
# macOS LaunchAgent 제거 스크립트

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_DEST="$HOME/Library/LaunchAgents/com.gikim.essay-shorts-retry.plist"

echo "프로젝트 경로: $PROJECT_DIR"

launchctl bootout "gui/$(id -u)" "$PLIST_DEST" >/dev/null 2>&1 || true
launchctl unload "$PLIST_DEST" >/dev/null 2>&1 || true
if [ -f "$PLIST_DEST" ]; then
    rm -f "$PLIST_DEST"
    echo "removed: $PLIST_DEST"
else
    echo "not present: $PLIST_DEST"
fi

echo "Local LaunchAgent automation removed."
echo "Daily uploads are now intended to run only from GitHub Actions at 07:00 KST."
