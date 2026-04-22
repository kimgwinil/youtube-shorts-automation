#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/kimgwonil/youtube-shorts-automation"
PLIST_NAME="com.kimgwonil.youtube-shorts-daily.plist"
SOURCE_PLIST="$PROJECT_DIR/launchd/$PLIST_NAME"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$PROJECT_DIR/logs"
cp "$SOURCE_PLIST" "$TARGET_PLIST"
launchctl unload "$TARGET_PLIST" >/dev/null 2>&1 || true
launchctl load "$TARGET_PLIST"
echo "installed: $TARGET_PLIST"
echo "start now: launchctl start com.kimgwonil.youtube-shorts-daily"

