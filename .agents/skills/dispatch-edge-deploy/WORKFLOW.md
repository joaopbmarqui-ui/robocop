# Dispatch Edge Deploy Workflow

Run from `D:\Projects\robocop` unless a command is explicitly remote.

## 1. Local Preflight

```powershell
git status --short --branch
git remote -v
git log --oneline --decorate --max-count=8
.\tools\dev\local_check.ps1
```

If the worktree is dirty, identify whether the dirt belongs to the current deployment work. Preserve unrelated user changes.

## 2. Publish a Bitbucket Snapshot

```powershell
git fetch bitbucket main
$source = (git rev-parse --short HEAD).Trim()
$parent = (git rev-parse bitbucket/main).Trim()
$tree = (git rev-parse 'HEAD^{tree}').Trim()
$date = Get-Date -Format 'yyyy-MM-dd HH:mm'
$message = "Deploy snapshot: Dispatch from robocop local main $source ($date)"
$snapshot = (git commit-tree $tree -p $parent -m $message).Trim()
git show --stat --oneline --no-renames --max-count=1 $snapshot
git push bitbucket ($snapshot + ':refs/heads/main')
git fetch bitbucket main
git log --oneline -1 bitbucket/main
```

If Soteri flags `PASSWORD_IN_URL`, inspect the lines. For documentation false positives, remove literal credential-in-URL examples and publish a new snapshot. Do not store embedded credentials in Git remote URLs.

## 3. Prepare Authenticated Edge Sessions

Inspect before sending commands:

```powershell
tmux ls
tmux capture-pane -t 0 -p -S -60
tmux capture-pane -t autobench_node04 -p -S -60
```

If SSH has auto-logged out, put each pane back at PASSCODE prompt:

```powershell
tmux send-keys -t 0 'ssh -p 2222 -o ServerAliveInterval=30 e176097@hde2stl020003.mastercard.int' Enter
tmux send-keys -t autobench_node04 'ssh -p 2222 -o ServerAliveInterval=30 e176097@hde2stl020004.mastercard.int' Enter
```

Wait for the user to authenticate and confirm both panes are at remote shell prompts.

## 4. Update Each Node

Prefer literal tmux injection for complex commands:

```powershell
$sha = '<snapshot-sha>'
$node03 = @'
cd /ads_storage/dispatch && echo __NODE03_DEPLOY_START__ && GIT_TERMINAL_PROMPT=0 git fetch bitbucket main && git reset --hard <snapshot-sha> && chmod 755 /ads_storage/dispatch && chmod -R a+rX /ads_storage/dispatch && chmod +x update.sh install.sh && PYBIN=$(command -v python3.11 || command -v python3.10 || command -v python3) && echo PYBIN:$PYBIN && $PYBIN -m compileall dispatch scr && DISPATCH_EMAIL=${DISPATCH_EMAIL:-e176097@mastercard.com} DISPATCH_PYTHON_BIN=$PYBIN ./install.sh && echo INSTALLED_VERSION && cat /ads_storage/$USER/.dispatch/installed_version && echo DISPATCH_HELP && ~/.local/bin/dispatch --help | head -8 && echo __NODE03_DEPLOY_END__
'@.Replace('<snapshot-sha>', $sha)
tmux send-keys -t 0 -l $node03
tmux send-keys -t 0 Enter
```

For node04, use session `autobench_node04` and replace the markers with `NODE04`.

Poll until end markers appear:

```powershell
tmux capture-pane -t 0 -p -S -160
tmux capture-pane -t autobench_node04 -p -S -160
```

## 5. Repair Broken Remote-Tracking Refs

If the remote fetch reports `cannot lock ref 'refs/remotes/bitbucket/main': unable to resolve reference`, run this in the affected remote checkout, then rerun the update:

```bash
cd /ads_storage/dispatch
git update-ref -d refs/remotes/bitbucket/main 2>/dev/null || true
rm -f .git/refs/remotes/bitbucket/main .git/logs/refs/remotes/bitbucket/main .git/packed-refs.lock
mkdir -p .git/refs/remotes/bitbucket .git/logs/refs/remotes/bitbucket
GIT_TERMINAL_PROMPT=0 git fetch bitbucket main
git reset --hard <snapshot-sha>
```

## 6. Prove `update.sh`

Run on each node after install:

```bash
cd /ads_storage/dispatch
GIT_TERMINAL_PROMPT=0 GIT_REMOTE=bitbucket GIT_BRANCH=main ./update.sh <snapshot-sha>
git log --oneline -1
git status --porcelain
cat /ads_storage/$USER/.dispatch/installed_version
~/.local/bin/dispatch --help | head -8
```

Expected evidence:

- HEAD is the snapshot SHA.
- `git status --porcelain` prints nothing.
- installed version prints the repo version.
- help output starts with `usage: dispatch [-h]`.

## 7. Shared Permissions

Apply on each node:

```bash
cd /ads_storage/dispatch
chmod 755 /ads_storage/dispatch
chmod -R a+rX /ads_storage/dispatch
chmod a+x /ads_storage/dispatch/*.sh /ads_storage/dispatch/scr/*.py
```

Verify with quote-free commands:

```bash
ls -ld /ads_storage/dispatch
ls -l /ads_storage/dispatch/*.sh /ads_storage/dispatch/scr/*.py
find /ads_storage/dispatch -type d ! -perm -001 -print | head -20
```

Expected evidence:

- `/ads_storage/dispatch` is `drwxr-xr-x` or more permissive.
- `install.sh`, `update.sh`, and `scr/*.py` are `-rwxr-xr-x` or more permissive.
- The non-world-traversable directory scan prints no paths.

## 8. Final Report

Include:

- local source commit
- Bitbucket snapshot SHA
- nodes updated
- local validation result
- remote compile/install/help result
- `update.sh` final verification result
- shared-permission evidence
- any repaired remote-state issue or auth handoff
