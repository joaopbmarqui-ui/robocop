# Operating-Model Conformance Investigation Plan

> **Status:** Local remediation applied on branch
> `codex/consolidated-user-story-pr23`; live node conformance probed from
> existing tmux sessions on 2026-06-23. This started as a read-only
> investigation plan and now records the repo-side fixes plus remaining
> live-environment gates.
> **Subject:** Does this repository (`robocop` / the Dispatch TUI) actually follow
> the Edge Node TUI operating model it documents in
> `docs/edge-node-tui-operating-model.md`?
> **Sibling reference:** The `autobench` project recently hardened its own
> deployment flow (Git-based `update.sh`, `reset --hard` sync, world-execute
> permissions, snapshot-publish discipline). This plan also checks whether
> robocop carries — or needs — those same refinements.

---

## 1. Purpose

Robocop is the **originating** project of the reusable Edge Node TUI operating
model. It *publishes* the model (`docs/edge-node-tui-operating-model.md`), so the
expectation is that robocop conforms to it closely. "It should be following it"
is the hypothesis; this plan is the structured way to **verify** that, identify
drift, and produce a per-node conformance verdict — without changing anything.

The investigation is strictly **read-only**: gather evidence, classify gaps, and
report. Any remediation is a separate, explicitly-approved follow-up.

## 2. Scope

In scope:
- The local repository at `D:\Projects\robocop` (config, scripts, docs, harness).
- The corporate deployment remote and commit identity/hook behavior.
- The deployed trees on each Edge Node (`/ads_storage/dispatch` on node 03 and
  node 04) — state, remote, permissions, line endings, drift.
- The production validation harness (`tools/prod_tui/`) and dev helpers
  (`tools/dev/`).

Out of scope (note but do not action here):
- Any fix, push, re-point, or resync.
- Product/feature behavior of the Dispatch TUI beyond what the harness exercises.

## 3. The operating model, distilled into testable tenets

Derived from `docs/edge-node-tui-operating-model.md`. Each becomes a checklist
item in Section 7.

1. **Committed Git state is the deployable source of truth** (file transfer is a
   fallback, not the source of truth).
2. **Four separated surfaces:** local dev machine; corporate Git remote; shared
   deployed tree (`/ads_storage/<tool>`); per-user runtime home
   (`/ads_storage/$USER/.<tool>`).
3. **Explicit remote roles:** a canonical review remote (GitHub) and a corporate
   deployment remote (`bitbucket`) reachable from both dev machine and nodes.
4. **Commit identity / hook strategy** documented (snapshot-remote pattern if the
   deployment remote is transport-only; never casual force-update).
5. **Non-interactive read-only credentials** on nodes: `GIT_TERMINAL_PROMPT=0 git
   fetch <remote> main` succeeds without a prompt.
6. **Idempotent `install.sh`** honoring the installer contract (per-user venv,
   preserves user state, writes `installed_version`, non-zero on missing
   prereqs, ABI-correct interpreter, no secrets).
7. **LF normalization** for Linux-bound files via `.gitattributes`
   (`*.py text eol=lf`, `*.sh text eol=lf`).
8. **Generated artifacts gitignored** (`*.zip`, `*.pyc`, `__pycache__/`,
   `tools/prod_tui/{screens,reports,logs}/`).
9. **Per-node independence:** each node deployed/verified separately; no claim
   infers one node's state from another; one harness config per node.
10. **Drift detection** answering local-vs-node and node-vs-node, ignoring
    `__pycache__`, with normalized line endings.
11. **Production tmux/SSH harness** with progressive safety levels and failure
    classification; never `Ctrl-C` as normal flow.
12. **Rollback is a Git operation + reinstall**, not manual file edits.
13. **Short, separate end-user `onboarding.md`**; the full doc set exists
    (`development-workflow`, `edge-node-first-time-setup`, `production-testing`,
    `edge-node-tui-operating-model`).

### 3a. Recent `autobench` refinements to check robocop against

These emerged while hardening autobench on the same nodes; robocop predates them
and its docs still describe the older flow:

- **R1 — `update.sh`:** a tracked updater doing `git fetch` + `git reset --hard
  <remote>/main` + `chmod -R a+rX`, preserving untracked `.venv/`/wheels.
  (Robocop currently documents `git checkout main` + `git pull --ff-only` +
  `install.sh` and appears to have **no `update.sh`**.)
- **R2 — `reset --hard` over `pull`:** guarantees content **and** LF endings
  **and** the executable bit match the repo; robocop's `pull --ff-only` can
  silently drift on permissions/CRLF.
- **R3 — World-execute permissions:** entrypoint scripts tracked `100755` and
  re-asserted with `chmod -R a+rX` each sync so *all* analysts can run them;
  shared dir tightened to `755` (not world-writable `777`).
- **R4 — Snapshot-publish discipline:** because the corporate remote has
  unrelated history and an author-only pre-receive hook, publish a single
  operator-authored deployment snapshot (`reset --soft <remote>/main` →
  commit → push) rather than `git push -u bitbucket HEAD`.

## 4. Preliminary static findings (2026-06-23, local read only — confirm on nodes)

These were observed from a quick static read and **must be validated**, not
trusted as conclusions:

- **F1 (HIGH) — RESOLVED: deployment remote was mis-wired; corrected to
  `dispatch.git`.** robocop's `bitbucket` remote had been set to
  `~e176097/autobench.git` (in `.git/config` and `docs/development-workflow.md`,
  hand-waved as a "naming artifact"). The owner confirmed the correct deployment
  repo for Dispatch is **`~e176097/dispatch.git`**; `autobench.git` belongs to
  the separate autobench tool (which was just pointed there with snapshot
  `5cb2fd3` on its `main`). On 2026-06-23 the local remote and the live
  docs/scripts (`development-workflow.md`, `edge-node-first-time-setup.md`,
  `tools/dev/git_sync_status.ps1`) were corrected to `dispatch.git`.
  **Two contamination risks remain — verify before any publish/resync:**
  - **dispatch.git history:** earlier this session, autobench deployment
    snapshots were mistakenly pushed to `~e176097/dispatch.git` (before the
    "dispatch is the wrong repo" correction for autobench). So `dispatch.git`
    `main` may currently hold an *autobench* tree, not robocop's. Audit it
    before publishing robocop.
  - **robocop nodes:** if node 03/04 `/ads_storage/dispatch` trees were ever
    pulled from `autobench.git` `main`, they may hold autobench code. Verify the
    deployed commit/tree on each node and reconcile before trusting them.
  (Historical records in `docs/dispatch_user_story_completion_audit.md` /
  `dispatch_user_story_tracker.csv` DOC-008 still describe the old "naming
  artifact" decision; they are point-in-time logs, left as-is but superseded.)
- **F2 (MED) — RESOLVED LOCALLY: `update.sh` / pre-refinement flow added.**
  Branch `codex/consolidated-user-story-pr23` adds tracked executable
  `update.sh`, which fetches the deployment remote, `git reset --hard`s the
  shared tree to the target ref, and reasserts shared read/execute permissions
  without `git clean` so untracked runtime/vendor artifacts survive. Active
  operator docs now prefer `update.sh` over `git pull --ff-only`, and
  `docs/development-workflow.md` documents operator-authored snapshot publish
  instead of casual `git push -u bitbucket HEAD`. **Live nodes do not have this
  updater until this branch is published and deployed.**
- **F3 (LOW/INFO) — Robocop is *ahead* in other areas.** It has a richer harness
  (`preflight.py`, levels 4–6, `controlled_job.py`, `robocop_tmux.py`) and an
  incremental-sync path (`tools/dev/edge_sync.ps1` → `_seam_deploy` with
  `verify`/`sync`/`deploy-all` modes) that autobench lacks. Conformance is
  bidirectional; capture what robocop does *better* too.
- **F4 — RESOLVED: `.gitattributes` confirmed.** The repo contains
  `*.py text eol=lf` and `*.sh text eol=lf`; `.gitignore` now includes
  `*.zip`, bytecode, and `tools/prod_tui/{screens,reports,logs}/`.

## 4a. Current remediation and live evidence (2026-06-23)

Local repo-side changes on this branch:

- Added `update.sh` as a tracked executable script.
- Updated `docs/development-workflow.md`,
  `docs/edge-node-first-time-setup.md`,
  `docs/edge-node-tui-operating-model.md`,
  `docs/production_testing.md`, and `tools/prod_tui/README.md` to prefer the
  reset-based update path.
- Updated zip deployment helpers to include and chmod `update.sh`.
- Added regression coverage in `tests/test_operating_model_conformance.py`.

Live node probes, using existing authenticated tmux sessions:

| Node | Session | Host | `/ads_storage/dispatch` state |
|---|---|---|---|
| node03 | `0` | `hde2stl020003.mastercard.int` | `HEAD == bitbucket/main == 51cc5f0f1e41a9050b02a3db94da53f6e47a7dcd`; `git status --porcelain` empty; `GIT_TERMINAL_PROMPT=0 git fetch bitbucket main` returned `0`; `/ads_storage/dispatch` is `drwxr-xr-x`; `install.sh` is `-rwxr-xr-x`; `file install.sh` reports ASCII shell script; `/ads_storage/e176097/.dispatch/installed_version` is `1.1.0`. |
| node04 | `autobench_node04` | `hde2stl020004.mastercard.int` | `HEAD == bitbucket/main == 51cc5f0f1e41a9050b02a3db94da53f6e47a7dcd`; `git status --porcelain` empty; `GIT_TERMINAL_PROMPT=0 git fetch bitbucket main` returned `0`; `/ads_storage/dispatch` is `drwxr-xr-x`; `install.sh` is `-rwxr-xr-x`; `file install.sh` reports ASCII shell script; `/ads_storage/e176097/.dispatch/installed_version` is `1.1.0`. |

Interpretation:

- F1 contamination is resolved for the observed live state: both nodes and
  `bitbucket/main` point at the Dispatch snapshot `51cc5f0`, not an autobench
  tree.
- The nodes are in sync with the currently deployed remote snapshot, but not
  with this local branch until the branch is published as a new deployment
  snapshot and each node runs `update.sh` followed by `install.sh`.
- Node credential state currently satisfies the model's non-interactive fetch
  check through stored HTTPS credentials. SSH deploy keys remain a possible
  future hardening, not a blocker for this branch.

## 5. Investigation objectives (questions to answer)

- Q1. RESOLVED for the 2026-06-23 live probe. `dispatch.git` `main` and both
  node 03/04 `/ads_storage/dispatch` trees hold Dispatch snapshot `51cc5f0`,
  not an autobench tree.
- Q2. Do the Edge Node deployed trees match committed Git state (zero drift),
  with correct LF endings and executable entrypoints?
- Q3. Can each node `git fetch` the deployment remote **non-interactively**
  (`GIT_TERMINAL_PROMPT=0`)?
- Q4. Does `install.sh` satisfy the installer contract, and is the per-user
  runtime home preserved across reruns?
- Q5. Are the repo hygiene tenets met (`.gitattributes` LF, `.gitignore`
  artifacts, full doc set, short onboarding)?
- Q6. Is per-node independence respected (one config per node, separate verify)?
- Q7. RESOLVED LOCALLY. Robocop should adopt R1-R4 for committed deployments.
  The branch adds `update.sh`, reset-hard sync, permission reassertion, and
  snapshot-publish documentation. `_seam_deploy` remains the fast authenticated
  session path and is documented as separate from committed deployments.

## 6. Methodology — phased, read-only

> Safety rules for every phase: **do not** push, re-point remotes, `reset`,
> `pull`, `chmod`, or `install` during the audit. Use `git fetch` (read-only),
> `git status`, `ls -l`, `git ls-files`, hashing, and `--dry-run` only. Never
> inject `Ctrl-C`. If a node SSH session is needed, reuse an authenticated
> session; expect interactive MFA and ask the operator to authenticate.

### Phase 0 — Local static audit (no node access)
- Inventory: `git -C D:\Projects\robocop remote -v`; list root scripts; confirm
  presence/absence of `update.sh`, `setup_remote_env.sh`, `run_tool.sh`.
- Read `.gitattributes`, `.gitignore`, `onboarding.md`, the four doc-set files,
  `install.sh`, `tools/dev/local_check.ps1`, `tools/dev/git_sync_status.ps1`,
  `tools/dev/edge_sync.ps1`, and `tools/prod_tui/` config templates + node
  configs.
- Record tracked file modes for entrypoints: `git -C D:\Projects\robocop ls-files
  -s -- "*.sh"` (look for `100644` vs `100755`).

### Phase 1 — Deployment remote & identity (resolve F1) — TOP PRIORITY
- Confirm the URL: `git -C D:\Projects\robocop remote get-url bitbucket`.
- Read-only reachability + what `main` resolves to:
  `git -c "http.extraHeader=Authorization: Bearer $env:BB_TOKEN" ls-remote
  bitbucket main` (operator-supplied token; never commit it).
- Compare that SHA/tree to **autobench**'s `bitbucket/main` (`5cb2fd3`). If they
  are the same repo/branch, document the collision and its blast radius
  precisely. Determine whether the projects are (a) genuinely sharing one repo,
  (b) expected to live on different branches, or (c) one is misconfigured.
- Check `gh` wiring: robocop docs say pass `-R pedrochagasmaster/robocop`
  explicitly. Confirm no command silently targets the wrong host.

### Phase 2 — Artifact & contract conformance (local)
- Map each tenet in Section 3 to evidence (Section 7 table).
- Validate `install.sh` against the installer contract and test cases
  (Section "Installer Test Cases" of the model): venv path, state preservation,
  `installed_version`, non-zero on missing Python, ABI-correct interpreter,
  launcher creation, idempotent profile update, runs from outside its dir.
- Confirm `.gitattributes` enforces LF for `*.py`/`*.sh`; confirm `.gitignore`
  covers zips, bytecode, and `tools/prod_tui/{screens,reports,logs}/`.

### Phase 3 — Edge Node live state (per node 03 and node 04, independently)
For each node (`hde2stl020003`, `hde2stl020004`, port 2222), in an
operator-authenticated session, at `/ads_storage/dispatch`:
- `git remote -v` (does it match the intended deployment repo?)
- `git log --oneline -1` and `git status --porcelain` (deployed commit + dirt)
- `GIT_TERMINAL_PROMPT=0 git fetch <remote> main` (Q3 — must not prompt)
- `git rev-parse HEAD` vs the remote/local expected SHA (drift)
- `ls -l *.sh` and `ls -ld /ads_storage/dispatch` (exec bits + dir mode;
  world-execute? world-writable?)
- Line-ending spot check on a shell script (e.g. `file install.sh`, or
  `cat -A install.sh | head` for CR markers)
- Per-user runtime home check: venv path under `/ads_storage/$USER/.dispatch`,
  `installed_version` present.
- **Never** infer node 04 from node 03; capture both separately.

### Phase 4 — Credentials (Q3)
- Determine the credential mechanism actually in use on each node (SSH deploy
  key vs stored HTTPS cred vs cache). Confirm against the model's preferred
  order. Flag any Git remote URL with embedded credentials as a finding.

### Phase 5 — Production harness conformance
- Run the **read-only** harness levels that do not mutate state, reusing an
  authenticated session:
  `py -m tools.prod_tui smoke --config tools/prod_tui/config-node04.yaml --level 1
  --reuse-session` (and node 03 config). Capture geometry, compile, TUI render,
  keybinding truth, failure classification.
- Confirm one harness config exists per node and that reports are written under
  the gitignored `tools/prod_tui/reports/`.

### Phase 6 — Gap analysis vs R1–R4
- For each of R1–R4, record: present / absent / partial, and whether adopting it
  would conflict with robocop's `_seam_deploy`/`edge_sync.ps1` model. Produce a
  recommendation (adopt / adapt / N/A) — as findings only, not actions.

## 7. Conformance checklist (fill during the audit)

| # | Tenet | Expected | How to verify | Node 03 | Node 04 | Local | Verdict |
|---|-------|----------|---------------|---------|---------|-------|---------|
| 1 | Git = source of truth | deployed tree == commit | drift hash | in sync with `51cc5f0` | in sync with `51cc5f0` | branch ahead of deployed snapshot | PASS for deployed state; pending publish for this branch |
| 2 | Four surfaces separated | venv in `/ads_storage/$USER/.dispatch` | `ls`, install.sh | runtime home present, `1.1.0` | runtime home present, `1.1.0` | installer preserves per-user home | PASS |
| 3 | Remote roles explicit | origin=GitHub, bitbucket=corp | `remote -v` | `dispatch.git` | `dispatch.git` | origin GitHub, bitbucket Dispatch | PASS |
| 4 | Identity/hook strategy | documented; snapshot if transport | docs + push test | n/a | n/a | snapshot publish documented | PASS locally; push remains explicit human action |
| 5 | Non-interactive fetch | no prompt | `GIT_TERMINAL_PROMPT=0 fetch` | rc 0 | rc 0 | n/a | PASS |
| 6 | Installer contract | per-user, idempotent, ABI-correct | contract review | installed version present | installed version present | mocked install smoke covered | PASS locally; real reinstall still manual gate |
| 7 | LF normalization | `*.py`/`*.sh eol=lf` | `.gitattributes`, `file` | `install.sh` ASCII shell script | `install.sh` ASCII shell script | rules present | PASS |
| 8 | Artifacts gitignored | zips/pyc/screens/reports/logs | `.gitignore` | n/a | n/a | covered by `.gitignore` | PASS |
| 9 | Per-node independence | 1 config/node, separate verify | configs + process | probed separately | probed separately | config per node | PASS |
| 10 | Drift detection | local vs node, node vs node | drift tool | clean porcelain | clean porcelain | `_seam_deploy verify` exists | PASS for deployed snapshot |
| 11 | Harness + levels | progressive, classified | run L1 | not rerun in this pass | not rerun in this pass | harness exists | PENDING real smoke |
| 12 | Rollback via Git | checkout/reset + reinstall | docs review | n/a | n/a | `update.sh <commit>` documented | PASS locally |
| 13 | Doc set + onboarding | all present, onboarding short | file check | n/a | n/a | present | PASS |
| R1 | `update.sh` | tracked updater | file check | pending deploy | pending deploy | added on branch | PASS locally |
| R2 | reset --hard sync | endings/exec match | sync method | pending deploy | pending deploy | `update.sh` uses reset-hard | PASS locally |
| R3 | World-execute perms | scripts `-rwxr-xr-x`, dir `755` | `ls -l` | PASS | PASS | `update.sh` reasserts | PASS |
| R4 | Snapshot publish | operator-authored snapshot | push flow | n/a | n/a | documented | PASS locally |

## 8. Evidence collection (commands — read-only)

Local (PowerShell; `;` separators, no `&&`):

```powershell
git -C D:\Projects\robocop remote -v
git -C D:\Projects\robocop remote get-url bitbucket
git -C D:\Projects\robocop ls-files -s -- "*.sh"
Get-Content D:\Projects\robocop\.gitattributes
Get-Content D:\Projects\robocop\.gitignore
# operator-supplied token; do not persist it
git -C D:\Projects\robocop -c "http.extraHeader=Authorization: Bearer $env:BB_TOKEN" ls-remote bitbucket main
```

Per node (operator-authenticated SSH session; read-only):

```bash
cd /ads_storage/dispatch
git remote -v
git log --oneline -1
git status --porcelain
GIT_TERMINAL_PROMPT=0 git fetch <deployment-remote> main   # must not prompt
git rev-parse HEAD
ls -l /ads_storage/dispatch/*.sh
ls -ld /ads_storage/dispatch
file /ads_storage/dispatch/install.sh
ls -l /ads_storage/$USER/.dispatch 2>/dev/null
```

## 9. Risks & safety

- **Do not** push, re-point remotes, `reset`, `pull`, `chmod`, or run
  `install.sh` during the audit — this is evidence-gathering only.
- **Contamination risk (F1).** `dispatch.git` may currently hold an autobench
  snapshot (mistakenly pushed earlier), and robocop nodes may hold autobench
  code if they pulled `autobench.git`. Do **not** publish robocop to
  `dispatch.git` or resync nodes until both are audited and reconciled. Keep
  autobench's publishes on `autobench.git` and robocop's on `dispatch.git`.
- Treat each node independently; never generalize one node's result.
- Never inject `Ctrl-C`; reuse authenticated sessions; expect MFA.
- Never log or commit tokens/passcodes; redact node captures (usernames, paths,
  hostnames) before sharing.

## 10. Deliverable

A short conformance report containing:
- The filled Section 7 table with per-node verdicts.
- A resolution of F1 (collision real / branch-separated / misconfig) with blast
  radius.
- A prioritized gap list (HIGH/MED/LOW), each with evidence and a recommended —
  but not yet executed — remediation, explicitly noting R1–R4 adopt/adapt/N/A.
- Per-node status lines in the model's format, e.g.
  `node03 IN_SYNC at <sha>` / `node04 DRIFT: <files>`.

## 11. Open questions for the repo owner

1. RESOLVED: the deployment remote is `~e176097/dispatch.git` (corrected
   2026-06-23), and the live probe found `dispatch.git` `main` plus both nodes
   on Dispatch snapshot `51cc5f0`.
2. RESOLVED LOCALLY: robocop should adopt `update.sh`, `reset --hard`,
   world-execute permission reassertion, and snapshot publish for committed
   deployments. `_seam_deploy` remains the fast authenticated-session path.
3. Are SSH deploy keys available for the nodes (the model's preferred
   non-interactive credential), or is HTTPS-with-cache the accepted reality?
