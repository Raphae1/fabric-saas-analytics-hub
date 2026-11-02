[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$CommitMessage
)

if (-not (Test-Path ".git")) {
    Write-Error "Error: This directory is not a Git repository. Run 'git init' first."
    exit 1
}

Write-Host "?? Checking Git status..." -ForegroundColor Cyan
$gitStatus = git status --porcelain

if (-not $gitStatus) {
    Write-Host "? No changes detected. Working tree is clean." -ForegroundColor Green
    exit 0
}

git status -s

if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $CommitMessage = Read-Host "Enter commit message (Press Enter for default 'Automated sync: $timestamp')"
    if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        $CommitMessage = "Automated sync: $timestamp"
    }
}

Write-Host "?? Staging changes..." -ForegroundColor Cyan
git add .

Write-Host "Committing with message: '$CommitMessage'..." -ForegroundColor Cyan
git commit -m "$CommitMessage"

if ($LASTEXITCODE -eq 0) {
    Write-Host "?? Pushing to remote repository (origin main)..." -ForegroundColor Cyan
    git push origin main

    if ($LASTEXITCODE -eq 0) {
        Write-Host "?? Successfully deployed changes to GitHub!" -ForegroundColor Green
    } else {
        Write-Error "? Git push failed. Please check your remote connection or authentication."
    }
} else {
    Write-Warning "?? Git commit skipped or failed."
}
