# PowerShell script to remove client secret file from git history

Write-Host "Starting removal of client secret file from git history..." -ForegroundColor Green

# Reset any ongoing operations
git reset --hard HEAD

# Remove the file from current index if it exists
git rm --cached --ignore-unmatch "auth/client_secret_292447687984-7ig33t4uv3j738g0mrkeg6tbm6hps8ds.apps.googleusercontent.com.json"

# Use filter-branch to remove from history
Write-Host "Running git filter-branch..." -ForegroundColor Yellow
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch 'auth/client_secret_292447687984-7ig33t4uv3j738g0mrkeg6tbm6hps8ds.apps.googleusercontent.com.json'" --prune-empty --tag-name-filter cat -- --all

# Clean up references
Write-Host "Cleaning up references..." -ForegroundColor Yellow
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin

# Clean up reflog and garbage collect
Write-Host "Cleaning up reflog and garbage collecting..." -ForegroundColor Yellow
git reflog expire --expire=now --all
git gc --prune=now --aggressive

Write-Host "File removed from git history successfully!" -ForegroundColor Green
Write-Host "You may need to force push if you've already pushed to remote: git push --force-with-lease" -ForegroundColor Cyan
