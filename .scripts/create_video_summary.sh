#!/usr/bin/env bash
#
# create_video_summary.sh
#
# This script:
# 1. Expects one argument: the YouTube video URL
# 2. Retrieves the video title (using youtube-dl or similar)
# 3. Cleans the title from symbols (only letters, numbers, spaces, and dashes allowed)
# 4. Creates an .md file in a hardcoded directory using the cleaned title
# 5. Copies a template file content into the new markdown file
# 6. Generates a summary from the given video URL (tries one command, if that fails tries another)
# 7. Appends the summary to the newly created markdown file
# 8. Appends a reference to the new file (wrapped in double-square-brackets) to a specific markdown file

# ------------------------------
#  Hardcoded paths / files
# ------------------------------
TARGET_DIR="/Users/user/Projects/ObsidianVaults/Aviad/Main/Knowledge/ArticlesSummaries"
TEMPLATE_FILE="/Users/user/Projects/ObsidianVaults/Aviad/Templates/Templates front matter.md"
INDEX_FILE="/Users/user/Projects/ObsidianVaults/Aviad/Main/Knowledge/ArticlesSummaries/Articles Summaries MOC.md"

# ------------------------------
#  Validate input
# ------------------------------
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <YouTube-URL>"
  exit 1
fi

VIDEO_URL="$1"

## Checking that yt-dlp is installed
if ! command -v yt-dlp &>/dev/null; then
  echo "yt-dlp is not installed. Please install it and try again."
  exit 1
fi

# ------------------------------
#  1. Retrieve video title
# ------------------------------
# Example: using youtube-dl (install if needed)
VIDEO_TITLE="$(yt-dlp --get-title "$VIDEO_URL" 2>/dev/null)"

if [ -z "$VIDEO_TITLE" ]; then
  echo "Could not retrieve video title. Check if yt-dlp is installed and the URL is correct."
  exit 1
fi

# ------------------------------
#  2. Clean the title
#    (Remove all non-alphanumeric except spaces and dashes)
# ------------------------------
CLEAN_TITLE="$(echo "$VIDEO_TITLE" | sed 's/[^a-zA-Z0-9 -]//g')"

# Replace multiple spaces with a single space (optional, but often useful):
CLEAN_TITLE="$(echo "$CLEAN_TITLE" | tr -s ' ')"

# ------------------------------
#  3. Create the new .md file
# ------------------------------
FILENAME="$TARGET_DIR/$CLEAN_TITLE.md"

# ------------------------------
#  4. Copy the template content
# ------------------------------
cp "$TEMPLATE_FILE" "$FILENAME"

# ------------------------------
#  5. Generate summary
# ------------------------------
SUMMARY=""

# First attempt
SUMMARY=$(fabric -y "$VIDEO_URL" --stream --pattern summarize 2>/dev/null | tee /dev/tty)
if [ $? -ne 0 ] || [ -z "$SUMMARY" ]; then
  # Second attempt if first fails
  SUMMARY=$(fabric -y "$VIDEO_URL" --stream --pattern summarize -m=gpt-4o-mini 2>/dev/null | tee /dev/tty)
fi

if [ -z "$SUMMARY" ]; then
  echo "Could not generate summary from either command."
  SUMMARY="No summary available."
fi

# Process the summary to change single # to ##
SUMMARY=$(echo "$SUMMARY" | sed 's/^# /## /')

# ------------------------------
#  6. Append summary to the new file
# ------------------------------
{
  echo ""
  echo "$VIDEO_URL"
  echo ""
  echo "$SUMMARY"
  echo ""
} >>"$FILENAME"

# ------------------------------
#  7. Append filename reference (wrapped in [[ ]]) to the index file
# ------------------------------
echo "[[$CLEAN_TITLE]]" >>"$INDEX_FILE"

OBSIDIAN_URL_FILENAME="obsidian://open?vault=Aviad&file=Main%2FKnowledge%2FArticlesSummaries%2F$CLEAN_TITLE"
OBSIDIAN_URL_FILENAME_ESCAPED=$(echo "$OBSIDIAN_URL_FILENAME" | sed 's/ /%20/g')

OBSIDIAN_URL_INDEX="obsidian://open?vault=Aviad&file=Main%2FKnowledge%2FArticlesSummaries%2FArticles%20Summaries%20MOC"

echo "Created summary file: $OBSIDIAN_URL_FILENAME_ESCAPED"
echo "Appended reference to: $OBSIDIAN_URL_INDEX"

open "$OBSIDIAN_URL_FILENAME_ESCAPED"
# open "$OBSIDIAN_URL_INDEX"

exit 0
