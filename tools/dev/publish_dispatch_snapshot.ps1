[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReviewedCommit,
    [string]$Remote = "bitbucket",
    [string]$Branch = "main",
    [switch]$RunLocalCheck,
    [switch]$LocalCheckPassed,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedBitbucketUrl = "https://scm.mastercard.int/stash/scm/~e176097/dispatch.git"
$TempBranch = "deploy/dispatch-snapshot"

function Invoke-GitText {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$GitArgs
    )

    $output = & git @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed: $output"
    }
    return ($output -join "`n").Trim()
}

function Invoke-Step {
    param(
        [string]$Description,
        [scriptblock]$Action
    )

    Write-Host $Description
    & $Action
}

function Invoke-OrPrint {
    param(
        [string]$Description,
        [scriptblock]$Action
    )

    if ($DryRun) {
        Write-Host "[dry-run] $Description"
        return
    }

    Invoke-Step $Description $Action
}

if (-not $RunLocalCheck -and -not $LocalCheckPassed) {
    throw "Choose either -RunLocalCheck or -LocalCheckPassed so the helper can verify the local gate."
}

if ($RunLocalCheck -and $LocalCheckPassed) {
    throw "Use only one of -RunLocalCheck or -LocalCheckPassed."
}

$repoRoot = Invoke-GitText rev-parse --show-toplevel
Set-Location $repoRoot

$currentBranch = Invoke-GitText branch --show-current
if ([string]::IsNullOrWhiteSpace($currentBranch)) {
    throw "Publishing from detached HEAD is not supported. Switch to the reviewed branch first."
}

$dirty = & git status --short
if ($dirty) {
    throw "Working tree must be clean before publishing a deployment snapshot."
}

$remoteUrl = Invoke-GitText remote get-url $Remote
if ($Remote -eq "bitbucket" -and $remoteUrl -ne $ExpectedBitbucketUrl) {
    throw "Remote '$Remote' does not match the expected Dispatch Bitbucket URL: $ExpectedBitbucketUrl"
}

$resolvedReviewedCommit = Invoke-GitText rev-parse --verify $ReviewedCommit
$remoteRef = "$Remote/$Branch"
$snapshotTimestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

if ($RunLocalCheck) {
    Invoke-OrPrint "Run .\tools\dev\local_check.ps1" {
        & powershell -NoProfile -ExecutionPolicy Bypass -File ".\tools\dev\local_check.ps1"
        if ($LASTEXITCODE -ne 0) {
            throw "tools/dev/local_check.ps1 failed with exit code $LASTEXITCODE"
        }
    }
}

Invoke-OrPrint "Fetch $Remote $Branch" {
    Invoke-GitText fetch $Remote $Branch | Out-Null
}

$previousRemoteCommit = Invoke-GitText rev-parse --verify $remoteRef
$snapshotMessage = "Deploy snapshot: Dispatch from robocop $resolvedReviewedCommit ($snapshotTimestamp)"
$summary = [ordered]@{
    timestamp = $snapshotTimestamp
    operation = "publish"
    remote = $Remote
    branch = $Branch
    reviewed_commit = $resolvedReviewedCommit
    previous_remote_commit = $previousRemoteCommit
    temporary_branch = $TempBranch
    dry_run = [bool]$DryRun
    status = if ($DryRun) { "not_applicable" } else { "passed" }
}

try {
    Invoke-OrPrint "Switch $TempBranch to $resolvedReviewedCommit" {
        Invoke-GitText switch -C $TempBranch $resolvedReviewedCommit | Out-Null
    }

    Invoke-OrPrint "Soft reset $TempBranch to $remoteRef" {
        Invoke-GitText reset --soft $remoteRef | Out-Null
    }

    Invoke-OrPrint "Create snapshot commit on $TempBranch" {
        Invoke-GitText commit -m $snapshotMessage | Out-Null
    }

    if (-not $DryRun) {
        $deploymentCommit = Invoke-GitText rev-parse --verify HEAD
        $summary["deployment_commit"] = $deploymentCommit
    }

    Invoke-OrPrint "Push HEAD:$Branch to $Remote" {
        Invoke-GitText push $Remote "HEAD:$Branch" | Out-Null
    }
}
finally {
    if (-not $DryRun) {
        Invoke-GitText switch $currentBranch | Out-Null
    }
}

if ($DryRun) {
    $summary["deployment_commit"] = "dry-run"
}

$summary | ConvertTo-Json -Depth 4
