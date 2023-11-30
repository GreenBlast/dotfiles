#!/bin/bash

# Function to search for node_modules directories recursively
search_node_modules() {
  find "$1" -type d -name "node_modules" -exec echo "Found node_modules in: {}" \; -prune
}

# Search for node_modules directories in all subdirectories of the current directory
search_node_modules .

echo "Script completed."

