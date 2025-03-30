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

  echo "Syncing from $SRC to $DEST..."
  rsync -av --delete --exclude=".git" --exclude=".git/*" "$SRC/" "$DEST/"
  # rsync -av --delete --exclude=".git" "$SRC/" "$DEST/"
  # rsync -av --delete "$SRC/" "$DEST/"
}

# Monitor both directories
fswatch -0 "$DIR1" "$DIR2" | while IFS= read -r -d "" event; do
  echo "Change detected: $event"

  # Determine which directory changed and sync accordingly
  if [[ "$event" == "$DIR1"* ]]; then
    sync_dirs "$DIR1" "$DIR2"
  elif [[ "$event" == "$DIR2"* ]]; then
    sync_dirs "$DIR2" "$DIR1"
  fi
done
