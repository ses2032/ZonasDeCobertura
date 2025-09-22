@echo off
echo Removing client secret file from git history...

REM First, let's reset any ongoing operations
git reset --hard HEAD

REM Remove the file from the index if it exists
git rm --cached --ignore-unmatch "auth/client_secret_292447687984-7ig33t4uv3j738g0mrkeg6tbm6hps8ds.apps.googleusercontent.com.json"

REM Use filter-branch to remove the file from history
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch 'auth/client_secret_292447687984-7ig33t4uv3j738g0mrkeg6tbm6hps8ds.apps.googleusercontent.com.json'" --prune-empty --tag-name-filter cat -- --all

REM Clean up
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo File removed from git history successfully!
echo You may need to force push if you've already pushed to remote: git push --force-with-lease
