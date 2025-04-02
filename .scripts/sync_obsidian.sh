#!/bin/bash

# Directories to sync
DIR1="/Users/user/Dropbox/sarcophagus/Obsidian/Aviad"
DIR2="/Users/user/Projects/ObsidianVaults/Aviad"

# Check if directories exist
if [ ! -d "$DIR1" ] || [ ! -d "$DIR2" ]; then
  echo "Error: One or both directories do not exist."
  exit 1
fi

echo "Monitoring $DIR1 and $DIR2 for changes..."

# Function to sync directories
sync_dirs() {
  echo "Syncing changes..."
  unison "$DIR1" "$DIR2" \
    -batch \
    -ignore "Name .git" \
    -ignore "Name *.swp" \
    -ignore "Name *.tmp" \
    -ignore "Name *~" \
    -ignore "Name .obsidian/workspace.json" \
    -prefer newer \
    -times \
    -silent
}

# Monitor both directories with debouncing
LAST_SYNC_TIME=0
DEBOUNCE_DELAY=3  # seconds

fswatch -0 "$DIR1" "$DIR2" | while IFS= read -r -d "" event; do
  CURRENT_TIME=$(date +%s)
  
  # Only sync if enough time has passed since last sync
  if (( CURRENT_TIME - LAST_SYNC_TIME >= DEBOUNCE_DELAY )); then
    sync_dirs
    LAST_SYNC_TIME=$CURRENT_TIME
  fi
done
