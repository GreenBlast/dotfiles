#!/bin/bash

# Function to delete node_modules directories recursively
# delete_node_modules() {
#   find . -type d -name "node_modules" -exec rm -rf {} +
# }

delete_node_modules() {
  find . -type d -name "node_modules" -exec rm -rf {} +
}

# Navigate through all subdirectories
for dir in */; do
  if [ -d "$dir" ]; then
    cd "$dir" || exit
    echo "Checking $dir..."
    delete_node_modules
    cd ..
  fi
done

echo "Script completed."
