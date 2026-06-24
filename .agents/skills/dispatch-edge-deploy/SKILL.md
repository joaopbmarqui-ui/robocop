---
name: dispatch-edge-deploy
description: Deploys this repo's Dispatch tree from local main to the corporate Bitbucket deployment remote and updates Hadoop Edge Node checkouts through authenticated tmux sessions. Use when the user asks to push Dispatch to Bitbucket, update edge nodes, deploy to node03/node04, run Edge Node smoke checks, or make remote /ads_storage/dispatch files executable for all users.
---

# Dispatch Edge Deploy

Use this skill for repo-specific Dispatch deployment work. It captures the known-good flow for publishing local `main` as a Bitbucket deployment snapshot, updating `/ads_storage/dispatch` on Edge Nodes, reinstalling the per-user command, smoke-testing, and fixing shared permissions.

For exact commands, use [WORKFLOW.md](WORKFLOW.md). Read it before touching the remote nodes.

## Deployment Model

- Local `main` is the source tree.
- `origin` is GitHub and is not the deployment target unless the user explicitly asks.
- `bitbucket` is the corporate remote the Edge Nodes can pull from.
- Bitbucket `main` may be a snapshot stream: create a commit whose tree is local `HEAD` and parent is current `bitbucket/main`.
- Edge Nodes update `/ads_storage/dispatch`, then users install/run from their own `/ads_storage/$USER/.dispatch` and `~/.local/bin/dispatch`.

## Standard Nodes

- node03: `hde2stl020003.mastercard.int`, often tmux session `0`
- node04: `hde2stl020004.mastercard.int`, often tmux session `autobench_node04`

Always inspect live tmux panes before sending commands. If SSH has auto-logged out, start SSH in the pane and let the user enter PASSCODE. Never handle PASSCODE in chat or scripts.

## Required Verification

Before publishing:

- `git status --short --branch`
- `git remote -v`
- `git log --oneline --decorate --max-count=8`
- `.\tools\dev\local_check.ps1`

After Bitbucket push:

- `git fetch bitbucket main`
- `git log --oneline -1 bitbucket/main`

On each node after update:

- `git log --oneline -1` is the deployed snapshot.
- `git status --porcelain` is empty.
- `python -m compileall dispatch scr` succeeds.
- `install.sh` reports Dispatch installed.
- `/ads_storage/$USER/.dispatch/installed_version` prints the expected version.
- `~/.local/bin/dispatch --help | head -8` prints the server-side TUI help.
- `./update.sh <snapshot-sha>` succeeds against the same SHA.
- Shared permissions are verified with `ls -ld`, `ls -l`, and a directory traversal scan.

## Operational Lessons

- Prefer `tmux capture-pane` and metadata before attaching or guessing.
- Use authenticated tmux sessions for Edge work; noninteractive SSH may fail on PASSCODE policy.
- Use `tmux send-keys -l` for commands containing quotes, globs, `$USER`, or `$(...)`; plain `send-keys` can mangle shell quoting.
- If a command lands in local PowerShell after SSH logout, stop, reauthenticate, and rerun remotely.
- If Git reports `cannot lock ref 'refs/remotes/bitbucket/main'`, repair the stale remote-tracking ref as documented in [WORKFLOW.md](WORKFLOW.md).
- If Soteri flags credential-shaped doc examples, inspect them. Remove false-positive literal examples and republish; never store credentials in remote URLs.

## Reporting

Report the exact Bitbucket snapshot SHA, local source commit, nodes updated, verification evidence, permission evidence, and any repaired remote-state issue.
