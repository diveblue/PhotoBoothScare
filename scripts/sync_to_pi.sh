#!/bin/bash
# Sync PhotoBoothScare project to Raspberry Pi
# - First tries rsync with excludes and delete
# - If rsync fails (e.g., protocol issues), falls back to tar-over-SSH (no delete)

set -u

SRC="/cygdrive/c/Users/Scott/OneDrive/Documents/Dev/Projects/PhotoBoothScare/"
DEST_HOST="scott@pi-photobooth"
DEST_PATH="photobooth/"   # relative to remote HOME (/home/scott)
# Optional: use rsync daemon instead of SSH if set to 1
USE_RSYNC_DAEMON=${USE_RSYNC_DAEMON:-0}
DEST_DAEMON="rsync://scott@pi-photobooth/photobooth/"

EXCLUDES=(
  --exclude '.venv'
  --exclude 'env'
  --exclude 'ENV'
  --exclude '__pycache__'
  --exclude '*.pyc'
  --exclude '.git'
  --exclude '.vscode'
  --exclude 'Website'
  --exclude 'Halloween2025Website'
)

echo "[sync] Attempting rsync to ${DEST_HOST}:${DEST_PATH} (SSH)..."
# Use a clean remote environment to avoid locale/profile output breaking the rsync protocol.
# -T disables TTY allocation. --rsync-path clears env and sets PATH and C locale explicitly.
if rsync -avz --delete -e "ssh -T" \
  --rsync-path="env -i LC_ALL=C LANG=C PATH=/usr/local/bin:/usr/bin:/bin rsync" \
  "${EXCLUDES[@]}" "$SRC" "${DEST_HOST}:${DEST_PATH}"; then
  echo "[sync] Sync complete via rsync."
  exit 0
fi

if [ "$USE_RSYNC_DAEMON" = "1" ]; then
  echo "[sync] SSH rsync failed. Trying rsync daemon at ${DEST_DAEMON}..."
  if rsync -avz --delete "${EXCLUDES[@]}" "$SRC" "$DEST_DAEMON"; then
    echo "[sync] Sync complete via rsync daemon."
    exit 0
  fi
fi

echo "[sync] rsync failed. Falling back to tar-over-SSH (no delete)."
echo "[sync] Creating remote directory if needed..."
ssh "${DEST_HOST}" "mkdir -p '${DEST_PATH}'" || {
  echo "[sync] ERROR: Unable to create remote path ${DEST_PATH}."; exit 1; }

echo "[sync] Streaming tar archive over SSH..."
# Tar from SRC with excludes and extract on remote. This will not delete removed files on the remote.
tar -C "$SRC" \
  --exclude='.venv' --exclude='env' --exclude='ENV' \
  --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.git' --exclude='.vscode' \
  --exclude='Website' --exclude='Halloween2025Website' \
  -czf - . | ssh "${DEST_HOST}" "tar -xzf - -C '${DEST_PATH}'"

STATUS=$?
if [ $STATUS -eq 0 ]; then
  echo "[sync] Sync complete via tar-over-SSH. (Note: deletions not propagated)"
else
  echo "[sync] ERROR: Fallback tar-over-SSH sync failed (exit $STATUS)."
  exit $STATUS
fi
