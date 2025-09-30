#!/bin/bash
# Clean deployment script for PhotoBoothScare to Raspberry Pi
# This script does a fresh deployment while preserving the virtual environment

set -e  # Exit on any error

# Configuration
SRC="/cygdrive/c/Users/Scott/OneDrive/Documents/Dev/Projects/PhotoBoothScare/"
DEST_HOST="scott@pi-photobooth"
DEST_PATH="photobooth"   # relative to remote HOME (/home/scott)
BACKUP_PATH="photobooth_venv_backup"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}[CLEAN DEPLOY] Starting fresh deployment to ${DEST_HOST}:${DEST_PATH}${NC}"

# Step 1: Backup the virtual environment if it exists
echo -e "${YELLOW}[STEP 1] Backing up virtual environment...${NC}"
ssh "${DEST_HOST}" "
  if [ -d '${DEST_PATH}/.venv' ]; then
    echo 'Virtual environment found, backing up...'
    rm -rf '${BACKUP_PATH}'
    mv '${DEST_PATH}/.venv' '${BACKUP_PATH}'
    echo 'Virtual environment backed up to ${BACKUP_PATH}'
  else
    echo 'No virtual environment found to backup'
  fi
"

# Step 2: Clean removal of old deployment (except .venv which we backed up)
echo -e "${YELLOW}[STEP 2] Cleaning old deployment...${NC}"
ssh "${DEST_HOST}" "
  if [ -d '${DEST_PATH}' ]; then
    echo 'Removing old deployment directory...'
    rm -rf '${DEST_PATH}'
  fi
  mkdir -p '${DEST_PATH}'
  echo 'Clean deployment directory created'
"

# Step 3: Deploy fresh code using tar-over-SSH
echo -e "${YELLOW}[STEP 3] Deploying fresh code...${NC}"
echo "Creating and transferring archive..."

# Create tar archive excluding unnecessary files and pipe to remote
tar -C "$SRC" \
  --exclude='.venv' \
  --exclude='env' \
  --exclude='ENV' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='.vscode' \
  --exclude='Website' \
  --exclude='Halloween2025Website' \
  --exclude='REORGANIZATION_SUMMARY.md' \
  --exclude='*.log' \
  --exclude='*.tmp' \
  -czf - . | ssh "${DEST_HOST}" "tar -xzf - -C '${DEST_PATH}'"

if [ $? -ne 0 ]; then
  echo -e "${RED}[ERROR] Code deployment failed!${NC}"
  exit 1
fi

# Step 4: Restore the virtual environment
echo -e "${YELLOW}[STEP 4] Restoring virtual environment...${NC}"
ssh "${DEST_HOST}" "
  if [ -d '${BACKUP_PATH}' ]; then
    echo 'Restoring virtual environment...'
    mv '${BACKUP_PATH}' '${DEST_PATH}/.venv'
    echo 'Virtual environment restored'
  else
    echo 'No virtual environment backup to restore'
    echo 'You may need to create a new virtual environment on the Pi'
  fi
"

# Step 5: Set proper permissions
echo -e "${YELLOW}[STEP 5] Setting permissions...${NC}"
ssh "${DEST_HOST}" "
  cd '${DEST_PATH}'
  find . -name '*.py' -exec chmod +x {} \;
  find . -name '*.sh' -exec chmod +x {} \;
  echo 'Permissions set'
"

# Step 6: Verify deployment
echo -e "${YELLOW}[STEP 6] Verifying deployment...${NC}"
ssh "${DEST_HOST}" "
  cd '${DEST_PATH}'
  echo 'Directory contents:'
  ls -la
  echo
  echo 'Python files in src/photobooth:'
  find src/photobooth -name '*.py' 2>/dev/null | head -10 || echo 'New structure deployed'
  echo
  if [ -d '.venv' ]; then
    echo 'Virtual environment: ✓ Present'
  else
    echo 'Virtual environment: ✗ Missing (needs setup)'
  fi
"

echo -e "${GREEN}[CLEAN DEPLOY] Fresh deployment completed successfully!${NC}"
echo
echo -e "${YELLOW}Next steps on the Pi:${NC}"
echo "1. ssh ${DEST_HOST}"
echo "2. cd ${DEST_PATH}"
echo "3. If .venv was missing, create it: python3 -m venv .venv"
echo "4. Activate: source .venv/bin/activate"
echo "5. Install/update requirements: pip install -r requirements.txt"
echo "6. Test: python photobooth.py --help"