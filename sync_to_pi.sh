#!/bin/bash
# Sync PhotoBoothScare project to Raspberry Pi, excluding local venv and cache files
# Does NOT overwrite or delete the venv on the Pi if it is not in the project folder

SRC="/cygdrive/c/Users/Scott/OneDrive/Documents/Dev/Projects/PhotoBoothScare/"
DEST="scott@pi-photobooth:photobooth/"

rsync -avz --delete \
  --exclude '.venv' \
  --exclude 'env' \
  --exclude 'ENV' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "$SRC" "$DEST"

echo "Sync complete!"
