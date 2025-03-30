#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <file_name> <source_directory> <destination_directory>"
  exit 1
fi

FILE_NAME="$1"
SOURCE_DIR="$2"
DEST_DIR="$3"

# Ensure the source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: Source directory '$SOURCE_DIR' does not exist."
  exit 1
fi

# Ensure the destination directory exists
if [ ! -d "$DEST_DIR" ]; then
  echo "Error: Destination directory '$DEST_DIR' does not exist."
  exit 1
fi

echo "Monitoring $SOURCE_DIR for $FILE_NAME..."
fswatch -0 "$SOURCE_DIR" | while IFS= read -r -d "" event; do
  if [ -f "$SOURCE_DIR/$FILE_NAME" ]; then
    echo "Detected $FILE_NAME. Moving it to $DEST_DIR..."
    mv "$SOURCE_DIR/$FILE_NAME" "$DEST_DIR"
  fi
done
