# Edge Node TUI Reuse Kit

A concise starter checklist for bootstrapping another Edge Node TUI from the
reusable operating model.

**Source of truth for rationale and depth:**
[`docs/edge-node-tui-operating-model.md`](edge-node-tui-operating-model.md)

**Do not copy product semantics from Dispatch** (job manifests, Kerberos gates,
Impala orchestration, queue limits, scratch schemas, fixture SQL, and so on).
Copy the **operating discipline only**: how code moves, how users install, how
operators verify, and how shared deployment state stays separate from per-user
runtime state.

Replace placeholders consistently: `<tool>`, `<Tool>`, `<repo-name>`, `<package>`,
`<entrypoint>`, `<deployment-remote>`, `<edge-node>`.

---

## When to use this kit

Use this kit when you are starting a **new** terminal UI that will:

- be developed on a local machine (often Windows),
- deployed to one or more Hadoop Edge Nodes over corporate Git,
- launched by users over SSH in a real terminal (tmux/psmux common),
- depend on cluster services (Kerberos, external CLIs) you cannot fully mock
  locally,
- need boring, repeatable operator workflows: install, drift check, smoke test,
  rollback.

Skip this kit if the tool is a local-only CLI, a web app, or does not need
per-node deployment and SSH-terminal validation.

**Golden path you are implementing:**

```text
local dev -> commit -> push corporate Git -> per-node fetch/checkout ->
install.sh -> drift zero -> tmux/SSH smoke -> record commit + report
```

---

## Files to create

Create these before calling the tool production-ready. Adapt names; keep the
roles.

| Role | Path | Purpose |
|------|------|---------|
| TUI package | `<package>/` | Application code and support modules |
| Installer | `install.sh` | Idempotent per-user install; preserves user state |
| Version stamp | `VERSION` | Deployed version written to user runtime home |
| End-user onboarding | `onboarding.md` | One page: where, install, launch, 2-3 fixes |
| Dev workflow | `docs/development-workflow.md` | Local loop, Git push, Edge update |
| Operator bootstrap | `docs/edge-node-first-time-setup.md` | Deploy key, shared tree, node inventory |
| Production testing | `docs/production-testing.md` | Harness levels, safety, failure classes |
| Operating assumptions | `docs/edge-node-tui-operating-model.md` | Filled copy of the neutral model (tool names) |
| Local gate | `tools/dev/local_check.ps1` (or equivalent) | Strongest safe local subset in one command |
| Sync/drift helper | `tools/dev/git_sync_status.ps1` (or equivalent) | Local vs remote byte compare |
| Prod harness | `tools/prod_tui/` | tmux/SSH driver, configs, reports |
| Per-node harness config | `tools/prod_tui/config-<edge-node>.yaml` | Host, repo path, geometry, SSH options |
| Node update script | `update.sh` (on shared tree) | `git fetch` + `git reset --hard`; no `git clean` |
| Dependencies | `pyproject.toml`, `requirements.txt` | Pinned runtime deps |
| Offline wheels | `vendor/` (optional) | Wheelhouse when Edge Nodes lack PyPI |
| Repo hygiene | `.gitattributes`, `.gitignore` | LF for `*.py`/`*.sh`; ignore reports/screens/zip |
| Product summary | `README.md` | What it is; pointers to install and run |

**Four surfaces to keep separate** (document each path in operator docs):

1. Local dev machine
2. Corporate Git remote (`<deployment-remote>`)
3. Shared deployed tree (e.g. `/ads_storage/<tool>`)
4. Per-user runtime home (e.g. `/ads_storage/$USER/.<tool>`)

---

## Commands and checks to adapt

Copy the **shape** of these commands; substitute tool-specific names, remotes,
and paths.

### Local development gate

```powershell
.\tools\dev\local_check.ps1
```

Typical Python Textual subset inside that script:

```powershell
py -m compileall <package> tools
py -m pytest tests tools/prod_tui/tests -q
py -m <package> --help
```

Provide a mock layer for Edge-only dependencies so local tests stay deterministic.

### Corporate Git remotes

```powershell
git remote add <deployment-remote> <corporate-git-url>
git remote -v
```

Pass repository explicitly to CLIs when multiple remotes exist.

### Non-interactive deploy pull (success criterion)

```bash
cd /ads_storage/<tool>
GIT_TERMINAL_PROMPT=0 git fetch <deployment-remote> main
```

If this prompts, fix credentials before relying on automation.

### Preferred Edge Node update

```bash
cd /ads_storage/<tool>
GIT_REMOTE=<deployment-remote> GIT_BRANCH=main ./update.sh
TOOL_PYTHON_BIN=$(command -v python3.11 || command -v python3.10) ./install.sh
```

For release validation or rollback, pin an exact commit:

```bash
GIT_REMOTE=<deployment-remote> GIT_BRANCH=main ./update.sh <commit-sha>
./install.sh
```

### Drift check (expect)

```text
MATCH=N  DRIFT=0  TOTAL=N
IN_SYNC
```

### Production harness (reuse authenticated session after human MFA)

```powershell
py -m tools.prod_tui smoke --config tools/prod_tui/config-<edge-node>.yaml --level all --reuse-session
```

### Rollback

```bash
cd /ads_storage/<tool>
git fetch <deployment-remote>
git checkout <previous-known-good-sha>
./install.sh
<tool> --help
```

### End-user path (keep language simple in `onboarding.md`)

```bash
cd /ads_storage/<tool>
./install.sh
export PATH="$HOME/.local/bin:$PATH"
cd /path/to/work
<tool>
```

Record every production promotion:

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

---

## Non-copyable product-specific values

Do **not** lift these from Dispatch or any sibling tool without re-validating
for the new product:

| Category | Examples (Dispatch-specific) | What to do instead |
|----------|------------------------------|--------------------|
| Paths and nodes | `/ads_storage/dispatch`, node03/node04 | Choose `<tool>` path; verify per-node filesystem sharing |
| Env var names | `DISPATCH_*`, `DISPATCH_DATA_ROOT` | Define `<TOOL>_*` or project-specific names |
| Package/entrypoint | `dispatch`, `python -m dispatch` | Use `<package>` and `<tool>` launcher |
| External CLIs | `impala-shell`, `klist` semantics tied to Impala jobs | List only CLIs your tool actually needs |
| Auth/workflow rules | max 2 running jobs, ticket TTL gates, queue names | Encode **your** product invariants separately |
| Harness fixtures | Dispatch SQL paths, mock scenarios, prefill JSON | Small named scratch fixtures safe to clean up |
| Smoke levels beyond L1-L3 | Table creation, CSV export decomposition | Define progressive levels for **your** workflows |
| Keyboard/help text | Dispatch footer bindings (`l` Logs, etc.) | Test advertised keys for **your** TUI |
| Git remotes | `bitbucket` URL, snapshot-publish discipline | Document **your** canonical vs deployment remote |
| Credentials | Deploy keys, SSH host aliases, operator emails | Generate new keys; never copy private material |
| Scratch data | Schemas, tables, queues, resource names | Use tool-owned test resources only |

The reusable asset is **operating discipline**, not Dispatch commands or domain
logic.

---

## Production readiness gates

Do not mark the tool production-ready until **all** gates pass.

### Repository and hygiene

- [ ] Layout matches the operating model (installer, docs set, harness, dev tools).
- [ ] `.gitattributes` enforces LF for Linux-bound `*.py` and `*.sh`.
- [ ] `.gitignore` excludes reports, screens, logs, zip bundles, bytecode.
- [ ] `VERSION` matches the tree you intend to deploy.

### Remotes and identity

- [ ] Corporate `<deployment-remote>` reachable from dev machine and each Edge Node.
- [ ] Canonical review remote (if any) role is documented separately from deploy remote.
- [ ] Commit author hooks on corporate remote are understood; snapshot strategy documented if needed.
- [ ] `GIT_TERMINAL_PROMPT=0 git fetch <deployment-remote> main` succeeds on each node without a prompt.

### Installer contract

- [ ] `install.sh` is idempotent; rerun preserves user config and state.
- [ ] Creates/refreshes venv under `/ads_storage/$USER/.<tool>/`.
- [ ] Writes `installed_version` from deployed `VERSION`.
- [ ] Installs from `vendor/` when wheels present; fails loudly on missing Python or required CLIs.
- [ ] Launcher at `~/.local/bin/<tool>`; prints PATH hint when needed.
- [ ] Tested from outside the repo directory.

### Per-node deployment

- [ ] Shared tree path documented per node in harness config inventory.
- [ ] Confirmed whether node filesystems are shared or independent (deploy/verify separately if independent).
- [ ] `update.sh` uses `git reset --hard` and does **not** `git clean`.
- [ ] Drift check reports `DRIFT=0` after update on **each** node.
- [ ] Node claims name the node and commit (never "prod is updated").

### Validation harness

- [ ] `tools/prod_tui/config-<edge-node>.yaml` per node (no hard-coded personal usernames in committed docs).
- [ ] Level 1 smoke: SSH/tmux alive, TUI opens, home renders, advertised keys work, help opens, quit clean.
- [ ] Level 2: installer, launcher, version match, required CLIs, Kerberos if applicable, writable runtime dir.
- [ ] Level 3: one tiny reversible controlled action on scratch resources only.
- [ ] Failure reports classify harness vs environment vs deployment vs TUI vs product workflow.
- [ ] Terminal geometry recorded (target 120x40 comfortable; handle 80x24 minimum).

### User-facing

- [ ] `onboarding.md` is one page, user language only (no Git/harness jargon).
- [ ] Rollback procedure documented and exercised once.
- [ ] No secrets in repo, docs, logs, or committed harness output.

### Release loop (mature workflow)

1. Local checks pass.
2. Commit and push to corporate Git.
3. On **each** Edge Node: fetch/checkout target commit, run `install.sh`.
4. Drift zero on each node.
5. Level 1/2 smoke (Level 3 if workflow changed).
6. Record deployed commit and report path.
7. Leave tmux/SSH session at a clean shell prompt.

If any step fails, stop and fix the workflow before users hit drift, stale
installs, credential prompts, or broken keybindings.

---

## Handoff prompt for another agent

Copy, fill placeholders, and attach to implementation work:

```text
You are bootstrapping a new Edge Node TUI using the operating discipline in
docs/edge-node-tui-operating-model.md and the checklist in
docs/edge-node-tui-reuse-kit.md.

Product: <Tool> (<one-line purpose>)
Package: <package>   CLI name: <tool>
Deployment remote: <deployment-remote>
Shared tree: /ads_storage/<tool>
User runtime: /ads_storage/$USER/.<tool>
Edge nodes: <list with independent vs shared storage noted>

Rules:
- Copy operating discipline only. Do NOT copy Dispatch product semantics,
  fixtures, env vars, or workflow rules.
- Implement the file set in "Files to create" before claiming production-ready.
- install.sh must be idempotent and preserve user state.
- Non-interactive git fetch must work on each node (GIT_TERMINAL_PROMPT=0).
- Per-node harness config + Level 1/2 smoke required; Level 3 only if you
  touch user workflows.
- LF normalization for .py and .sh; gitignore generated harness artifacts.
- Document rollback (git checkout + install.sh) and run drift check after deploy.

Deliverables:
1. Repo skeleton with installer, onboarding, docs set, local_check, prod_tui harness.
2. Filled docs/edge-node-tui-operating-model.md for this tool (names replaced).
3. Operator note: deploy key setup + node inventory table.
4. Evidence: local_check output, DRIFT=0 per node, smoke report paths.

Ask before inventing product-specific auth rules, external dependencies, or
smoke fixtures not listed above.
```

---

## Quick reference

| Need | Read |
|------|------|
| Why four surfaces, credential order, harness levels | `docs/edge-node-tui-operating-model.md` |
| What to create and in what order | This kit |
| Dispatch-specific implementation | Dispatch `README.md`, `onboarding.md`, `docs/development-workflow.md` (reference only) |
