# Clean deployment script for PhotoBoothScare to Raspberry Pi (PowerShell version)
# This script does a fresh deployment while preserving the virtual environment

param(
    [string]$DestHost = "scott@pi-photobooth",
    [string]$DestPath = "photobooth",
    [string]$BackupPath = "photobooth_venv_backup"
)

$SrcPath = "C:\Users\Scott\OneDrive\Documents\Dev\Projects\PhotoBoothScare"
$ErrorActionPreference = "Stop"

Write-Host "[CLEAN DEPLOY] Starting fresh deployment to $DestHost`:$DestPath" -ForegroundColor Green

# Step 1: Backup the virtual environment if it exists
Write-Host "[STEP 1] Backing up virtual environment..." -ForegroundColor Yellow
$backupCmd = @"
if [ -d '$DestPath/.venv' ]; then
    echo 'Virtual environment found, backing up...'
    rm -rf '$BackupPath'
    mv '$DestPath/.venv' '$BackupPath'
    echo 'Virtual environment backed up to $BackupPath'
else
    echo 'No virtual environment found to backup'
fi
"@

ssh $DestHost $backupCmd
if ($LASTEXITCODE -ne 0) { throw "Failed to backup virtual environment" }

# Step 2: Clean removal of old deployment
Write-Host "[STEP 2] Cleaning old deployment..." -ForegroundColor Yellow
$cleanCmd = @"
if [ -d '$DestPath' ]; then
    echo 'Removing old deployment directory...'
    rm -rf '$DestPath'
fi
mkdir -p '$DestPath'
echo 'Clean deployment directory created'
"@

ssh $DestHost $cleanCmd
if ($LASTEXITCODE -ne 0) { throw "Failed to clean old deployment" }

# Step 3: Deploy fresh code using scp
Write-Host "[STEP 3] Deploying fresh code..." -ForegroundColor Yellow

# Create temporary archive
$tempArchive = [System.IO.Path]::GetTempFileName() + ".tar.gz"
$excludePatterns = @(
    "--exclude=.venv",
    "--exclude=env", 
    "--exclude=ENV",
    "--exclude=__pycache__",
    "--exclude=*.pyc",
    "--exclude=.git",
    "--exclude=.vscode",
    "--exclude=Website",
    "--exclude=Halloween2025Website",
    "--exclude=REORGANIZATION_SUMMARY.md",
    "--exclude=*.log",
    "--exclude=*.tmp"
)

try {
    # Use WSL tar if available, otherwise use Windows tar
    if (Get-Command wsl -ErrorAction SilentlyContinue) {
        $srcPathWsl = $SrcPath -replace '^C:', '/mnt/c' -replace '\\', '/'
        wsl tar -C `"$srcPathWsl`" $excludePatterns -czf `"$tempArchive`" .
    } else {
        # Use Windows tar (available in Windows 10+)
        Push-Location $SrcPath
        tar $excludePatterns -czf $tempArchive .
        Pop-Location
    }
    
    if ($LASTEXITCODE -ne 0) { throw "Failed to create archive" }
    
    # Transfer and extract
    Write-Host "Transferring and extracting archive..."
    scp $tempArchive "$DestHost`:~/temp_deploy.tar.gz"
    if ($LASTEXITCODE -ne 0) { throw "Failed to transfer archive" }
    
    ssh $DestHost "cd '$DestPath' && tar -xzf ~/temp_deploy.tar.gz && rm ~/temp_deploy.tar.gz"
    if ($LASTEXITCODE -ne 0) { throw "Failed to extract archive" }
    
} finally {
    # Clean up temp file
    if (Test-Path $tempArchive) {
        Remove-Item $tempArchive -Force
    }
}

# Step 4: Restore the virtual environment
Write-Host "[STEP 4] Restoring virtual environment..." -ForegroundColor Yellow
$restoreCmd = @"
if [ -d '$BackupPath' ]; then
    echo 'Restoring virtual environment...'
    mv '$BackupPath' '$DestPath/.venv'
    echo 'Virtual environment restored'
else
    echo 'No virtual environment backup to restore'
    echo 'You may need to create a new virtual environment on the Pi'
fi
"@

ssh $DestHost $restoreCmd

# Step 5: Set proper permissions
Write-Host "[STEP 5] Setting permissions..." -ForegroundColor Yellow
$permCmd = @"
cd '$DestPath'
find . -name '*.py' -exec chmod +x {} \;
find . -name '*.sh' -exec chmod +x {} \;
echo 'Permissions set'
"@

ssh $DestHost $permCmd

# Step 6: Verify deployment
Write-Host "[STEP 6] Verifying deployment..." -ForegroundColor Yellow
$verifyCmd = @"
cd '$DestPath'
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
"@

ssh $DestHost $verifyCmd

Write-Host "[CLEAN DEPLOY] Fresh deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps on the Pi:" -ForegroundColor Yellow
Write-Host "1. ssh $DestHost"
Write-Host "2. cd $DestPath"
Write-Host "3. If .venv was missing, create it: python3 -m venv .venv"
Write-Host "4. Activate: source .venv/bin/activate"
Write-Host "5. Install/update requirements: pip install -r requirements.txt"
Write-Host "6. Test: python photobooth.py --help"