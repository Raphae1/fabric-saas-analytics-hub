# Deployment script for fabric-saas-analytics-hub
Write-Host "Starting deployment sync to GitHub..." -ForegroundColor Cyan

git status
git add .
$commitMsg = "Update multi-tenant analytics pipeline, FastAPI gateway, and security governance mapping - " + (Get-Date -Format "yyyy-MM-dd HH:mm")
git commit -m $commitMsg
git push origin main

Write-Host "Successfully synced changes to GitHub main branch!" -ForegroundColor Green
