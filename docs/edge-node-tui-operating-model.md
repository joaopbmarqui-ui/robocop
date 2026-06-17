# Edge Node TUI Operating Model

This document describes a reusable operating model for terminal UI tools that
are developed locally, deployed to Hadoop Edge Nodes, and used over SSH.

It is intentionally product-neutral. Replace `<tool>`, `<repo-name>`,
`<package>`, `<entrypoint>`, `<deployment-remote>`, and `<edge-node>` with the
names for a specific tool.

The target state is boring operations: one local development loop, one corporate
Git transport, one Edge Node deployed tree, one per-user installer, one short
onboarding path, and one production validation harness.

## How to Use This Document

Use this as a template when creating another Edge Node TUI. Copy the section
structure first, then fill in tool-specific names and checks.

Do not copy product semantics from an existing tool. Copy the operating model:
how code moves, how users install, how operators verify, and how credentials and
runtime state are separated.

Recommended companion docs for each tool:

- `README.md`: product summary, install pointer, run pointer.
- `onboarding.md`: short end-user install and launch flow.
- `docs/development-workflow.md`: developer loop and deployment workflow.
- `docs/edge-node-first-time-setup.md`: operator bootstrap guide.
- `docs/production-testing.md`: harness and safety levels.
- `docs/edge-node-tui-operating-model.md`: reusable operating assumptions.

## Golden Path

For normal development and deployment:

1. Develop and test locally.
2. Commit the change.
3. Push to the corporate Git remote.
4. On each Edge Node, fetch and checkout the target commit.
5. Run the per-user installer.
6. Verify node drift is zero.
7. Run production smoke checks through tmux/SSH.
8. Record the deployed commit and report path.

Every exception should be explicit. Zip upload, manual file sync, and direct
remote edits are fallback paths, not the default workflow.

## System Shape

An Edge Node TUI has four distinct surfaces:

1. **Local development machine**
   - Source code is edited here.
   - Unit tests and local mock tests run here.
   - Git commits are created here.
   - Bundles may be prepared here when Git pull is unavailable.
   - On Windows, use PowerShell-compatible commands and avoid assuming Bash
     syntax, heredocs, or `&&`.

2. **Corporate Git remote**
   - This is the durable transport layer from local development to Edge Nodes.
   - Edge Nodes should pull committed code from this remote.
   - Prefer a remote reachable from both the developer machine and Edge Nodes.
   - Avoid making ad hoc file copies the source of truth.

3. **Shared deployed tree on each Edge Node**
   - A shared path such as `/ads_storage/<tool>` or
     `/ads_storage/<repo-name>`.
   - Contains the checked-out source tree.
   - Contains pinned requirements, optional vendored wheels, installer, docs,
     and validation tooling.
   - May be a Git working tree.
   - May need to be deployed independently on each Edge Node.

4. **Per-user runtime home**
   - A user-owned path such as `/ads_storage/$USER/.<tool>`.
   - Contains the user's virtualenv, config, local state, logs, and cache.
   - Contains any durable runtime files that should survive reinstall.
   - Should not be overwritten by shared deployments.

Keep these surfaces separate. Shared code belongs in the deployed tree; mutable
user data belongs in the per-user runtime home; credentials should not be stored
in either unless explicitly designed and permissioned.

### Ownership Boundary

The deployed tree is owned by the tool operator or deployment workflow. The
runtime home is owned by the individual user.

This boundary is what makes `install.sh` safe to rerun. It can refresh code and
dependencies while preserving user config, history, logs, and runtime state.

## Edge Node Assumptions

Design for this environment:

- Users access the tool by SSHing into an Edge Node and running a terminal
  command.
- SSH commonly requires interactive MFA or RSA SecurID.
- Kerberos may be required separately after SSH login.
- The TUI runs inside a real terminal, often through VPN, SSH, tmux, or psmux.
- Network latency and terminal repaint costs are visible to users.
- Edge Nodes may have independent filesystems even if their paths look similar.
- Python may be available as `python3.10`, `python3.11`, or a corporate
  absolute path.
- Public internet access may be unavailable, so vendored wheels or internal
  package indexes may be required.
- Some users will have restricted permissions and should only write under their
  own `/ads_storage/$USER` tree.

Do not assume a GUI, browser, clipboard, mouse, local desktop notification, or
interactive prompts that can be automated safely.

### Design Consequence

The tool must be useful from a plain SSH terminal. Anything that requires a
desktop, browser callback, local file picker, system clipboard, or graphical
credential prompt should have a terminal-native fallback.

## Repository Layout

A reusable Edge Node TUI repository should have this high-level shape:

```text
<repo>/
  <package>/                  # TUI package and support modules
  tools/prod_tui/             # tmux/SSH production validation harness
  tools/dev/                  # local developer helper scripts
  docs/
    development-workflow.md   # local -> Git -> Edge Node workflow
    edge-node-first-time-setup.md
    production-testing.md
    edge-node-tui-operating-model.md
  install.sh                  # per-user installer
  onboarding.md               # short end-user setup page
  pyproject.toml
  requirements.txt            # pinned runtime dependencies
  vendor/                     # optional offline wheelhouse
  VERSION
  README.md
  .gitattributes
  .gitignore
```

The layout has three jobs:

- make the tool installable by a user without understanding the repo;
- make the deployed tree reproducible from Git;
- make production validation runnable without changing product code.

Recommended `.gitattributes`:

```gitattributes
*.py text eol=lf
*.sh text eol=lf
```

This matters when developing on Windows and deploying to Linux. If local files
use CRLF but Edge Node checkouts use LF, byte-level drift checks will report
false differences and shell scripts may fail remotely.

Recommended `.gitignore`:

```gitignore
*.zip
*.pyc
__pycache__/
.pytest_cache/
tools/prod_tui/screens/
tools/prod_tui/reports/
tools/prod_tui/logs/
```

Do not ignore source, docs, installer scripts, harness scripts, or config
templates. Ignore generated output and local credentials.

## Code Remotes

Keep remote roles explicit:

- A **canonical issue/review remote** may live in GitHub, GitLab, or another
  platform.
- A **corporate deployment remote** must be reachable from both the local
  development machine and the Edge Nodes.
- Name the deployment remote consistently, for example `bitbucket`.

Example:

```powershell
git remote add bitbucket <corporate-git-url>
git remote -v
```

For any CLI that infers a repository from `git remote -v`, pass the repository
explicitly if multiple remotes exist. This avoids accidentally filing issues,
creating PRs, or pushing to the wrong host.

Do not treat file transfer as the source of truth. File transfer is a fallback
or fast-iteration path. Committed Git state is the source of truth for
repeatable deployments.

### Commit Identity and Corporate Hooks

Corporate Git hosts may reject commits authored by service accounts, bots, or
unrecognized emails. Confirm this early.

If history cannot be pushed because older commits violate a hook, use one of
these deliberate strategies:

1. Fix authorship through the normal review process if preserving history
   matters.
2. Import the current tree as a single snapshot commit if the remote is only a
   deployment transport.
3. Push to a new branch and leave the default branch untouched until owners
   approve replacement.

Never force-update a shared branch casually. If a force update is required, use
`--force-with-lease` and record the old and new commit IDs.

### Snapshot Remote Pattern

Some deployment remotes are not the canonical history. They exist only so Edge
Nodes can pull a current tree.

In that model, the canonical repo keeps full history. The deployment remote can
hold a single snapshot commit authored by the operator. This satisfies strict
author hooks and keeps Edge pulls simple, but it means the deployment remote is
not a review archive.

Document which model the project uses.

## Credential Strategy

Interactive Git prompts on Edge Nodes are high-friction and break automation.
Prefer this order:

1. **Read-only SSH deploy key**
   - Best for non-interactive Edge Node pulls.
   - Key is scoped to the repository and read-only.
   - Private key is stored on the Edge Node with `0600` permissions.
   - Remote URL uses SSH, not HTTPS.

2. **Service account with read-only access**
   - Useful when SSH deploy keys are not available.
   - Token or credential is stored outside the repo, with restricted file
     permissions.

3. **Git credential helper/cache**
   - Acceptable for a single human operator, but less reproducible.
   - Make cache lifetime and storage explicit.

4. **Manual HTTPS username/password or token entry**
   - Use only as a bootstrap or emergency fallback.

Never embed tokens in scripts, docs, Git URLs, config files committed to the
repo, screenshots, logs, or agent prompts. If a token must exist on disk, put it
under a user-owned path, restrict permissions, and document how to rotate it.

### Credential Success Criteria

A healthy deployment checkout can run this without opening a prompt:

```bash
cd /ads_storage/<tool>
GIT_TERMINAL_PROMPT=0 git fetch <deployment-remote> main
```

If that command prompts or fails with an authentication error, the deployment
workflow is not mature yet. Fix credentials before relying on automated pulls.

## Deployment Topology

Treat each Edge Node as independent unless proven otherwise.

Even if both nodes use `/ads_storage/<tool>`, verify whether the filesystem is
actually shared. If it is not shared:

- deploy each node separately,
- run `install.sh` on each node,
- verify each node separately,
- capture reports per node,
- never infer one node's state from another node's state.

Maintain one config file per node in the production harness:

```yaml
host: "<user>@<edge-node>"
repo_path: "/ads_storage/<tool>"
session_name: "<tool>-prod-test-03"
terminal_width: 120
terminal_height: 40
ssh_options: "-p 2222 -o StrictHostKeyChecking=no"
operator_email: ""
```

Avoid hard-coding personal usernames in reusable docs. Keep personal values in
local config files, environment variables, or user-specific overrides.

### Node Inventory

Each tool should maintain a small operator-owned inventory:

```text
node          config file                           deployed path
<node-a>      tools/prod_tui/config-<node-a>.yaml   /ads_storage/<tool>
<node-b>      tools/prod_tui/config-<node-b>.yaml   /ads_storage/<tool>
```

The inventory should also state whether the deployed path is shared or
independent. If it is independent, every production claim must name the node.

Good:

```text
<node-a> IN_SYNC at <commit>
<node-b> IN_SYNC at <commit>
```

Bad:

```text
prod is updated
```

## Installer Contract

Every Edge Node TUI should provide an idempotent `install.sh` that can be run
again after every deployment.

The installer should:

- resolve a supported Python interpreter,
- create or refresh a per-user virtualenv under `/ads_storage/$USER/.<tool>/venv`,
- install pinned dependencies from `vendor/` when present,
- fall back to a configured internal or public package index only when allowed,
- preserve existing user config and state,
- create a launcher under `~/.local/bin/<tool>`,
- add `~/.local/bin` to the user's shell profile if needed,
- write `installed_version` from the deployed `VERSION`,
- print the exact next command for the current shell if `PATH` is not refreshed,
- exit non-zero on missing prerequisites.

The installer should not:

- require `source install.sh`,
- overwrite user config on rerun,
- store secrets,
- assume the current working directory unless it explicitly resolves its own
location,
- depend on a graphical prompt,
- silently continue after a failed dependency install.

End-of-install output should be direct:

```bash
<Tool> installed.
To use <tool> in this shell now:
  export PATH="$HOME/.local/bin:$PATH"
Then cd to your working directory and run: <tool>
```

If the current shell already has `~/.local/bin` on `PATH`, say that the command
is available now.

### Installer Skeleton

The exact implementation can vary, but the shape should stay familiar:

```bash
#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
USER_NAME=${USER:-$(id -un)}
DATA_ROOT=${TOOL_DATA_ROOT:-/ads_storage/$USER_NAME}
TOOL_HOME="$DATA_ROOT/.<tool>"
PYTHON_BIN=${TOOL_PYTHON_BIN:-}

if [ -z "$PYTHON_BIN" ]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3.11)
  elif command -v python3.10 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3.10)
  else
    echo "Python 3.10+ not found" >&2
    exit 1
  fi
fi

mkdir -p "$TOOL_HOME"
"$PYTHON_BIN" -m venv "$TOOL_HOME/venv"

if [ -n "$(find "$ROOT_DIR/vendor" -maxdepth 1 -name '*.whl' -print -quit 2>/dev/null)" ]; then
  "$TOOL_HOME/venv/bin/pip" install \
    --no-index \
    --find-links="$ROOT_DIR/vendor" \
    -r "$ROOT_DIR/requirements.txt"
else
  "$TOOL_HOME/venv/bin/pip" install -r "$ROOT_DIR/requirements.txt"
fi

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/<tool>" <<EOF
#!/bin/bash
export PYTHONPATH="$ROOT_DIR"
exec "$TOOL_HOME/venv/bin/python" -m <package> "\$@"
EOF
chmod +x "$HOME/.local/bin/<tool>"

cp "$ROOT_DIR/VERSION" "$TOOL_HOME/installed_version"
echo "<Tool> installed."
```

This skeleton is intentionally incomplete. Add tool-specific config creation,
prerequisite checks, and user-facing messages, but keep the same boundaries.

### Installer Test Cases

At minimum, test these behaviors:

- first install creates the virtualenv and launcher;
- rerun preserves existing config and state;
- missing Python exits non-zero with a useful message;
- missing required external CLI exits non-zero;
- installer writes `installed_version`;
- launcher runs `<tool> --help`;
- shell profile update is idempotent;
- installer works when called from outside its own directory.

## User Onboarding Pattern

End-user onboarding should be one page, separate from operator/deployment docs.

It should answer only:

1. Where do I go?
2. What command do I run?
3. How do I launch the TUI?
4. What are the two or three common fixes?

Recommended structure:

```markdown
# <Tool> Onboarding

## Install

cd /ads_storage/<tool>
./install.sh

## Launch

cd /path/to/my/work
<tool>

## Quick Checks

export PATH="$HOME/.local/bin:$PATH"
which <tool>
klist
```

Keep advanced deployment concepts out of the end-user page. Users should not
need to know about Git remotes, vendored wheels, branch names, validation
harnesses, or rollback procedures just to start the TUI.

### Onboarding Tone

Use user language, not deployment language.

Prefer:

```text
Run this once.
Open a new SSH session.
Go to your working directory.
Run <tool>.
```

Avoid:

```text
Clone the repository, install dependencies, source the profile, validate the
remote, and inspect the deployment tree.
```

If the user needs an operator, say exactly what to send:

```text
If this still fails, send the installer output and the result of `which <tool>`
to the tool owner.
```

## Usage Pattern for SSH TUIs

Design user usage around this mental model:

```text
ssh edge-node
kinit                 # if the tool depends on Kerberos-backed services
cd /path/to/work
<tool>
```

Inside the TUI:

- keyboard must be enough; mouse is optional,
- primary actions should be visible in footer/help,
- `?` should show contextual help,
- `q` should quit cleanly from the top screen,
- `Esc` should return/back out of sub-screens,
- long operations must show status and must not freeze the UI,
- terminal disconnects should not corrupt persisted state,
- logs and diagnostics should be reachable without leaving the TUI.

Avoid relying on `Ctrl-C` as normal flow. In terminal multiplexers and harnesses
it may kill sessions, leave pty state dirty, or be routed somewhere unexpected.
Prefer explicit quit/back actions.

## Local Development Loop

Local development should have a single command that exercises the strongest
safe subset:

```powershell
.\tools\dev\local_check.ps1
```

For a Python Textual TUI, a typical gate is:

```powershell
py -m compileall <package> tools
py -m pytest tests tools/prod_tui/tests -q
py -m <package> --help
```

When the tool depends on Edge Node services, provide a mock layer or fake
wrappers for local development. Local tests should cover deterministic behavior;
the production harness should cover SSH, Kerberos, real terminal rendering, and
Edge Node dependencies.

Use `pyproject.toml` dev extras for test dependencies:

```toml
[project.optional-dependencies]
dev = [
  "pytest",
  "pytest-asyncio",
]
```

First-time local setup:

```powershell
py -m pip install -e ".[dev]"
```

## Deployment Paths

Use three deployment paths, each with a clear purpose.

### 1. Git Pull on the Edge Node

Preferred for committed, reviewable deployments:

```bash
cd /ads_storage/<tool>
git fetch <deployment-remote>
git checkout main
git pull --ff-only <deployment-remote> main
TOOL_PYTHON_BIN=$(command -v python3.11 || command -v python3.10) ./install.sh
```

Use a tool-specific variable name in real projects, for example
`ANALYZER_PYTHON_BIN` or `REPORT_TUI_PYTHON_BIN`. The generic examples use
`TOOL_PYTHON_BIN` only as a placeholder.

Use exact commit checkout for release validation or rollback:

```bash
git fetch <deployment-remote>
git checkout <commit-sha>
./install.sh
```

For production promotion, exact commits are better than branch names. Branch
names are convenient; commit IDs are auditable.

Recommended update record:

```text
node=<edge-node>
path=/ads_storage/<tool>
remote=<deployment-remote>
commit=<sha>
version=<VERSION>
installer_exit=0
drift=0
report=<path>
```

### 2. Incremental Sync Over an Authenticated Session

Useful for fast iteration when:

- a human already opened an authenticated SSH/tmux session,
- the change is small,
- the change does not need to become the canonical deployment yet,
- the sync tool verifies drift and validates syntax remotely.

This path should always print what it changed and should back up overwritten
remote files. It is a development accelerator, not a substitute for Git.

Incremental sync tools should have three modes:

```text
verify      compare local and remote, do not write
sync        deploy ordinary runtime files only
deploy-all  deploy all tracked runtime files, including sensitive/shared scripts
```

If a tool has high-risk runtime scripts, make `sync` refuse them by default and
require an explicit flag or mode for full parity.

### 3. Full Bundle Upload

Use for:

- first-time setup,
- offline installs,
- vendor wheel refreshes,
- disaster recovery,
- environments where Git access from the Edge Node is unavailable.

Build one archive with Linux-safe paths. Do not rely on Windows zip behavior
that writes backslash paths if the target is Linux.

Generated bundles are artifacts and should be ignored by Git.

Bundle upload should still end in the same state as Git pull:

1. deployed tree updated,
2. `install.sh` run,
3. version recorded,
4. drift verified where possible,
5. smoke checks run.

If a bundle path skips these steps, it is not equivalent to the normal
deployment path.

## Drift Detection

Provide a way to answer:

- Does `<node-a>` match local?
- Does `<node-b>` match local?
- Do `<node-a>` and `<node-b>` match each other?
- Which files drifted?

For Python tools, a simple MD5 comparison over deployed `.py` files is often
enough, but only if line endings are normalized. Report:

```text
MATCH=28  DRIFT=0  TOTAL=28
IN_SYNC
```

The verifier should:

- compare the files that matter for runtime,
- ignore `__pycache__`,
- include shared runtime scripts if they are deployed with the tool,
- skip generated logs/reports/screens,
- make it obvious when a file exists only locally or only remotely.

## Production TUI Harness

Plain subprocess tests are not enough for a real TUI. The harness should drive
the tool the way users do:

```text
local machine
  tmux or psmux session
    pane: ssh -p <port> <user>@<edge-node>
      remote shell
        kinit
        cd /ads_storage/<tool>
        <tool>
```

Control happens locally:

- create/capture/resize local tmux window,
- send keys to the local tmux pane,
- capture terminal text,
- attach for manual takeover,
- reuse an authenticated session for checks that cannot perform MFA
non-interactively.

Production validation levels should be generic and progressive:

1. **Level 1: safe TUI smoke**
   - SSH/tmux session is alive.
   - Expected terminal geometry or minimum viable geometry is present.
   - Package compiles on the Edge Node.
   - TUI opens.
   - Home screen renders.
   - Advertised key navigation works.
   - Help opens.
   - Quit returns cleanly to the shell.

2. **Level 2: real environment checks**
   - Installer runs.
   - Launcher resolves.
   - Runtime version matches deployed version.
   - Kerberos state is detected if applicable.
   - Required external CLIs are on `PATH`.
   - User runtime directory is writable.
   - Terminal rendering is clean over SSH.

3. **Level 3: controlled action**
   - Only a tiny, known, reversible action.
   - Scoped to scratch/test resources.
   - Cleanup attempted.
   - Preconditions checked before execution.

4. **Higher levels**
   - Broader feature matrix.
   - Persistence/supervision behavior.
   - Failure modes.
   - Soak/upgrade checks.

Never let a harness launch arbitrary user work as a smoke test. Test fixtures
must be small, known, named, and safe to clean up.

### Harness Failure Classes

Classify failures so operators know what to fix:

- **Harness setup failure:** tmux missing, psmux broken, config wrong, SSH
  session gone, passcode prompt still visible.
- **Environment failure:** Python missing, installer failed, external CLI
  missing, Kerberos missing, storage not writable.
- **Deployment failure:** wrong commit, version mismatch, drift detected,
  missing files, stale virtualenv.
- **TUI behavior failure:** app opens but a key does not work, a screen fails to
  render, quit/back leaves the pane stuck.
- **Product workflow failure:** controlled action fails even though the TUI and
  environment are healthy.

A good JSON report should make this classification obvious.

### Terminal Geometry

Terminal geometry is part of the product contract. The harness should record the
geometry it tested.

For fresh sessions, create the tmux window at the configured size. For reused
sessions, try to resize and then verify. If the multiplexer refuses to resize,
report the actual geometry and decide whether it is acceptable for that run.

Do not hide geometry failures. A TUI can pass at 120x40 and fail at 88x53. Both
results are useful, but they mean different things.

### Keybinding Truth

The harness should test advertised keys, not just internal actions.

If the footer says `l Logs`, then pressing `l` from the home screen should open
Logs. If it does not, treat that as a product or focus-routing bug even if the
screen can be opened through another route.

This catches the most common TUI drift: help text, footer bindings, and actual
focus behavior disagree.

## Session Reuse

MFA makes fully automated login difficult. Harness commands should support both:

- start a new session when a passcode is provided,
- reuse an already-authenticated session.

Use reuse mode after a human logs in and runs `kinit`:

```powershell
py -m tools.prod_tui smoke --config tools/prod_tui/config-<node>.yaml --level all --reuse-session
```

When reusing sessions:

- verify the session exists before running checks,
- verify the pane is at a shell prompt,
- return cleanly from any TUI screen before running shell commands,
- check terminal geometry and resize if the terminal/mux supports it,
- do not inject `Ctrl-C` as the normal escape path.

If the terminal multiplexer cannot resize a reused session reliably, either
document the accepted geometry or start a fresh correctly-sized session before
validation.

## Authentication and Secrets

There are usually three separate authentication concerns:

1. SSH into the Edge Node.
2. Kerberos for cluster services.
3. Git credentials for deployment pulls.

Treat them separately. A working SSH session does not imply Kerberos is healthy;
a Kerberos ticket does not imply Git can pull.

Recommended checks:

```bash
klist
git ls-remote <deployment-remote> main
which <required-cli>
```

Rules:

- Never log passcodes, passwords, or tokens.
- Never paste credentials into scripts that will be committed.
- Prefer SSH keys or deploy keys for non-interactive Git pulls.
- Keep credentials out of terminal captures when possible.
- Redact generated reports before sharing outside the immediate operator group
  if they may include usernames, paths, resource names, or internal hostnames.

## Remote Git Pull Without Human Prompts

For repeatable operation, configure the Edge Node checkout to use SSH:

```bash
cd /ads_storage/<tool>
git remote set-url <deployment-remote> ssh://git@<git-host>/<project>/<repo>.git
```

Store the private key outside the repository:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
chmod 600 ~/.ssh/<tool>_deploy_key
```

Use an SSH config entry:

```sshconfig
Host <tool>-git
  HostName <git-host>
  User git
  IdentityFile ~/.ssh/<tool>_deploy_key
  IdentitiesOnly yes
```

Then set the remote to the host alias:

```bash
git remote set-url <deployment-remote> <tool>-git:<project>/<repo>.git
git fetch <deployment-remote>
```

If corporate policy requires HTTPS, use a credential helper approved for the
Edge Node environment. Do not store cleartext tokens in the repo or in shared
paths.

### Deploy Key Setup Runbook

Use this as the operator flow when SSH deploy keys are allowed:

1. Generate or request a read-only key for the repository.
2. Register the public key in the corporate Git host with read-only access.
3. Copy the private key to each Edge Node under the operator/user account that
   performs pulls.
4. Set `chmod 600` on the private key and `chmod 700` on `~/.ssh`.
5. Add an SSH config host alias.
6. Change the Git remote to use that host alias.
7. Run `GIT_TERMINAL_PROMPT=0 git fetch <deployment-remote> main`.
8. Document the rotation owner and expiry/renewal process.

Validation command:

```bash
ssh -T <tool>-git
cd /ads_storage/<tool>
GIT_TERMINAL_PROMPT=0 git fetch <deployment-remote> main
```

The exact `ssh -T` output depends on the Git host. The important property is
that it does not prompt.

### HTTPS Credential Helper Runbook

If SSH is unavailable and HTTPS is mandatory:

```bash
git config --global credential.helper 'cache --timeout=28800'
git fetch <deployment-remote> main
```

This reduces repeated prompts during one operator session, but it is not a full
automation solution. Prefer an approved secure store or service identity if the
tool must update without a human present.

Do not use:

```bash
https://user:token@host/path/repo.git
```

URLs with embedded credentials leak through shell history, process lists,
terminal captures, Git config, and support screenshots.

## Rollback

Rollback should be a normal Git operation plus reinstall:

```bash
cd /ads_storage/<tool>
git fetch <deployment-remote>
git checkout <previous-known-good-sha>
./install.sh
<tool> --help
```

After rollback:

- verify `installed_version`,
- run Level 1/2 smoke,
- run any controlled action needed to confirm the affected workflow,
- record the deployed commit in the incident or change log.

Do not roll back by manually editing files unless Git is unavailable. If manual
edits are made during an emergency, run drift detection afterward and reconcile
the deployed tree back to Git.

## Observability and Artifacts

Generated artifacts should be predictable and ignored by Git:

```text
tools/prod_tui/screens/
tools/prod_tui/reports/
tools/prod_tui/logs/
*.zip
*.pyc
__pycache__/
```

Reports should include:

- node,
- timestamp,
- deployed commit,
- tool version,
- check names,
- pass/fail status,
- last captured screen on failure,
- enough command output for diagnosis without exposing secrets.

Keep artifacts local unless they are explicitly needed for review. Screens can
include internal paths, usernames, and resource names.

## TUI Design Constraints for Edge Nodes

Reusable Edge Node TUI rules:

- render correctly at 80x24 or show a clear resize message,
- prefer 120x40 as the comfortable validation size,
- keep the home screen useful over slow SSH,
- minimize recurring repaint and filesystem work,
- show state with text labels, not color alone,
- keep keybindings stable and visible,
- keep `q`, `Esc`, `?`, arrows, and `Tab` predictable,
- use async workers or background processes for slow operations,
- never block the UI thread on network, Kerberos, Git, filesystem scans, or
  external CLIs,
- preserve user state across terminal disconnects if the tool starts long work,
- write logs where users and operators can find them.

For Textual specifically:

- keep styling in a stylesheet,
- use workers for subprocesses and file I/O,
- do not mutate widgets from threads,
- clean up workers on screen exit,
- test with Textual pilot locally and tmux/SSH remotely.

## What to Replicate

Replicate these patterns across tools:

- committed Git state as the deployable source of truth;
- per-node update and verification;
- per-user runtime home under `/ads_storage/$USER`;
- idempotent installer;
- short end-user onboarding;
- local mock/development layer;
- production tmux/SSH harness;
- byte-level drift verification;
- non-interactive read-only Git credentials on Edge Nodes;
- explicit rollback through Git checkout plus reinstall;
- LF normalization for Linux-bound source and shell scripts;
- generated reports/screens/logs ignored by Git.

## What Not to Replicate Blindly

Do not copy these details without re-validating them for the new tool:

- exact node names;
- exact deployed path;
- exact scratch schemas, queues, tables, or resource names;
- exact test fixture data;
- exact smoke levels beyond the generic shape;
- exact keyboard shortcuts if the new TUI has different workflows;
- exact package names or environment variable names;
- human user credentials;
- assumptions that both Edge Nodes share storage;
- assumptions that tmux/psmux can resize reused sessions;
- assumptions that HTTPS Git credentials will stay cached.

The reusable asset is the operating discipline, not the product-specific
commands.

## First-Time Project Checklist

For a new Edge Node TUI, create these before production use:

- `install.sh` with idempotent per-user install.
- `onboarding.md` with a short end-user path.
- `docs/development-workflow.md` with local -> Git -> Edge update flow.
- `docs/edge-node-first-time-setup.md` for operators.
- `docs/production-testing.md` for harness usage and safety levels.
- `tools/dev/local_check.ps1` or equivalent.
- `tools/dev/git_sync_status.ps1` or equivalent.
- Production harness config per Edge Node.
- Local mock layer for dependencies not available off-cluster.
- `.gitattributes` enforcing LF for Linux-bound files.
- `.gitignore` for reports, logs, screens, zip bundles, and bytecode.
- Corporate Git remote reachable from Edge Nodes.
- Non-interactive read-only Git credential strategy.
- Rollback command documented and tested.
- Smoke test report format.

## Mature Workflow Checklist

Use this as the release/update loop:

1. Run local checks.
2. Commit the change.
3. Push to corporate Git.
4. On each Edge Node, fetch and checkout the target commit.
5. Run `install.sh`.
6. Verify deployed file drift is zero.
7. Run Level 1/2 smoke.
8. Run controlled action checks if the change touches user workflows.
9. Record the deployed commit and report path.
10. Leave the session in a clean shell state.

If any step fails, stop and fix the workflow before continuing. A mature Edge
Node TUI workflow is valuable because it fails early and visibly, before users
discover drift, stale installs, credential prompts, or broken keybindings.