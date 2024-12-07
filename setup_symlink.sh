#!/bin/bash

# Configuration
PROJECT_DIR="/Users/ehsanolyaee/Documents/Code/intelli-deck-addon/src/intelli_deck_addon"
ANKI_ADDONS_DIR="/Users/ehsanolyaee/Library/Application Support/Anki2/addons21/intelli_deck_addon"

# Create the addon directory if it doesn't exist
mkdir -p "$ANKI_ADDONS_DIR"

# Remove existing symlink or directory if it exists
rm -rf "$ANKI_ADDONS_DIR"

# Create the symlink
ln -s "$PROJECT_DIR" "$ANKI_ADDONS_DIR"
echo "Symlink created/updated successfully." 
