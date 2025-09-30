#!/usr/bin/env powershell
# Test script to verify clean deployment approach for PhotoBoothScare

param(
    [string]$DestHost = "scott@pi-photobooth",
    [switch]$DryRun = $false
)

Write-Host "=== PhotoBoothScare Clean Deploy Test ===" -ForegroundColor Cyan
Write-Host "Target: $DestHost" -ForegroundColor Yellow
Write-Host "Dry Run: $DryRun" -ForegroundColor Yellow
Write-Host ""

# Test SSH connectivity
Write-Host "[TEST 1] Testing SSH connectivity..." -ForegroundColor Green
try {
    $result = ssh $DestHost "echo 'SSH connection successful'; hostname; whoami; pwd"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ SSH connection successful" -ForegroundColor Green
        Write-Host $result
    } else {
        throw "SSH connection failed"
    }
} catch {
    Write-Host "✗ SSH connection failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test current deployment state
Write-Host "[TEST 2] Checking current deployment state..." -ForegroundColor Green
$checkCmd = @"
echo "Current photobooth directory:"
if [ -d 'photobooth' ]; then
    ls -la photobooth/ | head -10
    echo ""
    echo "Virtual environment status:"
    if [ -d 'photobooth/.venv' ]; then
        echo "✓ .venv exists"
        echo "Python version in venv:"
        photobooth/.venv/bin/python --version 2>/dev/null || echo "✗ venv python not working"
    else
        echo "✗ .venv missing"
    fi
    echo ""
    echo "Current structure:"
    find photobooth -type d -maxdepth 2 2>/dev/null | head -10
else
    echo "✗ No photobooth directory found"
fi
"@

ssh $DestHost $checkCmd

Write-Host ""

if (-not $DryRun) {
    Write-Host "[READY] Run the clean deployment with:" -ForegroundColor Cyan
    Write-Host "  .\scripts\clean_deploy_to_pi.ps1" -ForegroundColor White
} else {
    Write-Host "[DRY RUN] Would proceed with clean deployment" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan