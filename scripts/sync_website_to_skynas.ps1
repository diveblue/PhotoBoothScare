# Push website code back to SKYNAS
# Updates the Halloween2025 website on the SKYNAS server
# PowerShell version for Windows

param(
    [switch]$DryRun = $false
)

$SrcDir = "Website"
$DestUNC = "\\SKYNAS\web\Halloween2025"

Write-Host "[website-sync] Pushing website code to SKYNAS..." -ForegroundColor Cyan

# Check if source directory exists
if (-not (Test-Path $SrcDir)) {
    Write-Host "[website-sync] ERROR: Source directory '$SrcDir' not found" -ForegroundColor Red
    exit 1
}

# Check if destination is accessible
if (-not (Test-Path $DestUNC)) {
    Write-Host "[website-sync] ERROR: Cannot access SKYNAS at '$DestUNC'" -ForegroundColor Red
    Write-Host "[website-sync] Make sure SKYNAS is accessible and you have permissions" -ForegroundColor Yellow
    exit 1
}

Write-Host "[website-sync] Source: $SrcDir" -ForegroundColor Green
Write-Host "[website-sync] Destination: $DestUNC" -ForegroundColor Green

if ($DryRun) {
    Write-Host "[website-sync] DRY RUN - No files will be modified" -ForegroundColor Yellow
    $RobocopyArgs = @(
        $SrcDir,
        $DestUNC,
        "/E",           # Copy subdirectories including empty ones
        "/XD", "media", # Exclude media directory
        "/L",           # List only (dry run)
        "/NP",          # No progress
        "/NDL",         # No directory list
        "/NJH",         # No job header
        "/NJS"          # No job summary
    )
} else {
    $RobocopyArgs = @(
        $SrcDir,
        $DestUNC,
        "/E",           # Copy subdirectories including empty ones
        "/XD", "media", # Exclude media directory
        "/PURGE",       # Delete files in destination that don't exist in source
        "/NP",          # No progress
        "/NDL"          # No directory list
    )
}

Write-Host "[website-sync] Running robocopy..." -ForegroundColor Cyan
$Process = Start-Process -FilePath "robocopy.exe" -ArgumentList $RobocopyArgs -Wait -PassThru -NoNewWindow

# Robocopy exit codes: 0-3 are success, >3 are errors
if ($Process.ExitCode -le 3) {
    Write-Host "[website-sync] Website successfully synced to SKYNAS!" -ForegroundColor Green
    
    if (-not $DryRun) {
        Write-Host "[website-sync] Your website is now live at: https://diveblue.synology.me/index.php" -ForegroundColor Cyan
    }
    
    exit 0
} else {
    Write-Host "[website-sync] ERROR: Robocopy failed with exit code $($Process.ExitCode)" -ForegroundColor Red
    exit 1
}