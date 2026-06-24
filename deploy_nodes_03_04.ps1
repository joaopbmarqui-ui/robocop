# Interactive deploy to edge nodes 03 and 04.
# Run inside tmux so you can enter RSA when SSH prompts.
# One SSH session per node (zip streamed over stdin; no ControlMaster — unsupported on Windows).

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$RemoteUser = "e176097"
$RemotePort = 2222
$RemotePath = "/ads_storage/dispatch"
$ZipName = "dispatch_deploy.zip"
$SetupScript = "install.sh"
$UpdateScript = "update.sh"

if (-not (Test-Path $ZipName)) {
    Write-Error "Missing $ZipName. Run deploy_and_install.ps1 steps 1-2 first."
    exit 1
}

$version = (Get-Content VERSION -Raw).Trim()
Write-Host "=== Dispatch deploy: nodes 03 + 04 ===" -ForegroundColor Cyan
Write-Host "Bundle version: $version"
Write-Host "Zip: $ZipName ($((Get-Item $ZipName).Length) bytes)"
Write-Host ""
Write-Host "Enter your RSA passcode once per node when SSH prompts." -ForegroundColor Yellow
Write-Host ""

function Assert-LastExitCode {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed (exit $LASTEXITCODE)"
    }
}

function Deploy-ToNode {
    param([string]$Suffix)

    $remoteServer = "hde2stl0200${Suffix}.mastercard.int"
    $remoteTarget = "${RemoteUser}@${remoteServer}"
    $remoteZip = "$RemotePath/$ZipName"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " NODE $Suffix  ($remoteServer)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    Write-Host "[1/1] Uploading, installing, and verifying in one SSH session (RSA prompt)..."
    $remoteCommand = "set -eu && " +
        "mkdir -p $RemotePath && " +
        "echo '--- Receiving $ZipName ---' && " +
        "cat > $remoteZip && " +
        "cd $RemotePath && " +
        "echo '--- Unzipping artifacts ---' && " +
        "python3 -m zipfile -e $ZipName . && " +
        "echo '--- Verifying extraction ---' && " +
        "ls -F && " +
        "echo '--- Running Setup ---' && " +
        "chmod +x $SetupScript $UpdateScript && " +
        "DISPATCH_PYTHON_BIN=`$(command -v python3.11 || command -v python3.10) ./$SetupScript && " +
        "echo '--- Verifying dispatch ---' && " +
        "~/.local/bin/dispatch --help | head -5 && " +
        "echo '---' && " +
        "cat $RemotePath/VERSION"

    $zipPath = Join-Path $PSScriptRoot $ZipName
    cmd /c "ssh -p $RemotePort -o StrictHostKeyChecking=accept-new $remoteTarget `"$remoteCommand`" < `"$zipPath`""
    Assert-LastExitCode "deploy on node $Suffix"

    Write-Host "Node $Suffix done." -ForegroundColor Green
}

try {
    Deploy-ToNode "03"
    Deploy-ToNode "04"
    Write-Host ""
    Write-Host "=== ALL DEPLOYMENTS SUCCESSFUL ===" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "=== DEPLOYMENT FAILED ===" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""
Write-Host "Press Enter to close this pane..."
Read-Host
