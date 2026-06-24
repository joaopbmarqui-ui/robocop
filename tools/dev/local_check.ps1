[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Name,
        [string[]]$Command
    )

    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
    Write-Host ($Command -join " ")
    $exe = $Command[0]
    $args = if ($Command.Count -gt 1) { $Command[1..($Command.Count - 1)] } else { @() }
    & $exe @args
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

$repoRoot = (& git rev-parse --show-toplevel 2>&1)
if ($LASTEXITCODE -ne 0) {
    throw "Run this script from inside the Dispatch git repository."
}

Set-Location (($repoRoot -join "`n").Trim())

$localTemp = Join-Path $PWD ".local-check-tmp"
$pytestTemp = Join-Path $PWD ".local-check-pytest"

Invoke-Step "Compile Python sources" @("py", "-m", "compileall", "dispatch", "scr")
New-Item -ItemType Directory -Force $localTemp | Out-Null
$oldTemp = $env:TEMP
$oldTmp = $env:TMP
try {
    $env:TEMP = $localTemp
    $env:TMP = $localTemp
    Invoke-Step "Run unit tests" @(
        "py", "-m", "pytest", "tests", "tools/prod_tui/tests", "-q",
        "--basetemp", $pytestTemp
    )
}
finally {
    $env:TEMP = $oldTemp
    $env:TMP = $oldTmp
    Remove-Item -LiteralPath $localTemp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $pytestTemp -Recurse -Force -ErrorAction SilentlyContinue
}
Invoke-Step "Dispatch help smoke" @("py", "-m", "dispatch", "--help")

Write-Host ""
Write-Host "Local check passed." -ForegroundColor Green
