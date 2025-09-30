#!/bin/bash
# Push website code back to SKYNAS
# Updates the Halloween2025 website on the SKYNAS server

set -u

SRC_DIR="Website"
DEST_UNC="//SKYNAS/web/Halloween2025"
DEST_PATH="/mnt/skynas/Halloween2025"  # For Linux mounting

echo "[website-sync] Pushing website code to SKYNAS..."

# Check if we're on Windows (Cygwin/Git Bash) or Linux
if [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" ]]; then
    # Windows environment - use robocopy
    echo "[website-sync] Using Windows robocopy..."
    cmd.exe /c "robocopy \"$SRC_DIR\" \"$DEST_UNC\" /E /XD media /PURGE"
    RESULT=$?
    
    # Robocopy exit codes: 0-3 are success, >3 are errors
    if [ $RESULT -le 3 ]; then
        echo "[website-sync] Website successfully synced to SKYNAS via robocopy"
        exit 0
    else
        echo "[website-sync] ERROR: Robocopy failed with exit code $RESULT"
        exit 1
    fi
    
else
    # Linux environment - try rsync to mounted share
    echo "[website-sync] Using Linux rsync..."
    
    # Check if SKYNAS is mounted
    if [ ! -d "$DEST_PATH" ]; then
        echo "[website-sync] ERROR: SKYNAS not mounted at $DEST_PATH"
        echo "[website-sync] Please mount SKYNAS first:"
        echo "  sudo mkdir -p /mnt/skynas"
        echo "  sudo mount -t cifs //SKYNAS/web /mnt/skynas -o username=your_user,password=your_pass"
        exit 1
    fi
    
    # Sync with rsync, excluding media folder and preserving everything else
    if rsync -avz --delete \
        --exclude 'media/' \
        --exclude 'media' \
        "$SRC_DIR/" "$DEST_PATH/"; then
        echo "[website-sync] Website successfully synced to SKYNAS via rsync"
        exit 0
    else
        echo "[website-sync] ERROR: rsync failed"
        exit 1
    fi
fi