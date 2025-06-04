#!/bin/bash

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' not found"
    exit 1
fi

# Convert HTML to Markdown using pandoc
cat "$input_file" | pandoc -f html -t markdown-raw_html+backtick_code_blocks --wrap none > out.md

# Check if pandoc conversion was successful
if [ $? -ne 0 ]; then
    echo "Error: Pandoc conversion failed"
    exit 1
fi

# Clean the markdown using Python script
python ~/.scripts/clean_markdown_converted_from_medium.py ./out.md ./cleaned_file.md

# Check if Python script execution was successful
if [ $? -ne 0 ]; then
    echo "Error: Python cleaning script failed"
    exit 1
fi

# Open the cleaned file in Sublime Text
open -a "Sublime Text" cleaned_file.md
