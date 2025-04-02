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

# Function to sync from one directory to the other
sync_dirs() {
  SRC="$1"
  DEST="$2"

  # Add a delay to allow file operations to complete
  sleep 2

  echo "Syncing from $SRC to $DEST..."
  rsync -av --delete --exclude=".git" --exclude=".git/*" "$SRC/" "$DEST/"
  # rsync -av --delete --exclude=".git" "$SRC/" "$DEST/"
  # rsync -av --delete "$SRC/" "$DEST/"
  # rsync -av --delete --update \
  #   --exclude=".git" --exclude=".git/*" \
  #   --exclude="*.swp" --exclude="*.tmp" --exclude="*~" \
  #   --exclude=".obsidian/workspace.json" \
  #   --delay-updates \
  #   --modify-window=2 \
  #   "$SRC/" "$DEST/"
}

# Monitor both directories with debouncing
LAST_SYNC_TIME=0
DEBOUNCE_DELAY=3  # seconds

fswatch -0 "$DIR1" "$DIR2" | while IFS= read -r -d "" event; do
  CURRENT_TIME=$(date +%s)
  
  # Only sync if enough time has passed since last sync
  if (( CURRENT_TIME - LAST_SYNC_TIME >= DEBOUNCE_DELAY )); then
    echo "Change detected: $event"

    # Determine which directory changed and sync accordingly
    if [[ "$event" == "$DIR2"* ]]; then
      sync_dirs "$DIR2" "$DIR1"
    elif [[ "$event" == "$DIR1"* ]]; then
      sync_dirs "$DIR1" "$DIR2"
    fi
    
    LAST_SYNC_TIME=$CURRENT_TIME
  fi
done
