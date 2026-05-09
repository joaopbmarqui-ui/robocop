# Dispatch — Implementation Plan

This document is the consolidated specification for migrating the **Hadoop
Query Launcher** from a Windows GUI (`run_query.ps1`) to a server-side TUI
named **Dispatch** running directly on the Hadoop edge node. It synthesises
the design conversation into a single reference for implementers.

It assumes the reader has already read [`CONTEXT.md`](../CONTEXT.md) for the
domain language and the architectural decisions in
[`docs/adr/`](./adr/).

---

## 1. Vision

Today, running a long Impala query is a multi-system ritual: open a Windows
GUI on a workstation, fill a form, watch it scp a file, paste a generated
command into a separately-launched ssh terminal, and trust the email
notifications. Dispatch collapses that ritual into one server-side TUI.
Users `ssh` to the edge node, `cd` to where their `.sql` files live, run
`dispatch`, fill a form, and walk away. **Jobs** survive ssh disconnects
because they're owned by an out-of-process runner, not by the TUI itself.

Dispatch reuses the production-tested orchestrator scripts in `scr/` as the
queue-cycling, retrying, email-notifying engine — they remain a frozen
black-box API for v1.0 and are subject to surgical, mock-validated changes
thereafter (ADR-0005).

---

## 2. What changes for users

| Today | After Dispatch v1.0 |
|---|---|
| Double-click `run_query_engine.bat` on Windows | Run `dispatch` from any directory on the edge node |
| Form fields point at a local Windows path | Form is CWD-aware: shows `*.sql` in `$PWD` |
| `scp` step uploads SQL | No `scp`; the SQL is already on the server |
| Manual `kinit` after ssh; orchestrator fails late if you forgot | TUI pre-flights `klist`; TTL is shown live; in-TUI `kinit` via terminal-suspend |
| Terminal window IS the live tail; closing it loses the tail | Job dashboard reattaches the live tail at any time |
| Four named workflows with hidden mode-flag interactions | Two orthogonal axes — `Source` × `Destination` — with greyed-out illegal cells |
| No way to see "what's running for me" | First-class Job dashboard + 7-day history |
| CSV results come back as `.csv.gz` over `scp` | CSV lands uncompressed in `$PWD` |
| One Job per "Launch" click; no concurrency awareness | Hard cap of 2 Running Jobs per user |

---

## 3. Domain model

See [`CONTEXT.md`](../CONTEXT.md) for canonical definitions. Headline:

A **Job** is `(Source, Destination, params)`. **Source** is one of `SqlFile`
/ `SqlTemplate` / `ExistingTable`. **Destination** is one of `Table` / `Csv`
/ `Table + Csv`. Five legal cells in the matrix; each maps to one or two
calls to an **Orchestrator script** in `scr/`.

| Source ↓ / Destination → | Table | Csv | Table + Csv |
|---|---|---|---|
| `SqlFile` | `Query_Impala_Parametrized.py` | `download_to_csv.py --query-file` | both, sequenced |
| `SqlTemplate` | `monthly_query_processor.py` | — | — |
| `ExistingTable` | — | `download_to_csv.py --table-name` | — |

`SqlTemplate + Csv` is intentionally absent — monthly outputs are for
downstream analytical use, not bulk CSV export.

---

## 4. Architectural decisions

| ADR | Decision |
|---|---|
| [0001](./adr/0001-jobs-as-on-disk-manifests.md) | **Jobs are on-disk manifests under `/ads_storage/<user>/.dispatch/jobs/`.** A small stdlib runner script owns the lifecycle; the TUI is read-only over the directory. |
| [0002](./adr/0002-textual-for-the-tui.md) | **Textual is the TUI framework**, vendored as wheels and installed into a per-user venv. The orchestrators keep their stdlib-only policy. |
| [0003](./adr/0003-csv-output-uncompressed-in-user-cwd.md) | **CSVs land uncompressed in the user's launch-time CWD.** The runner decomposes `Table + Csv` into two orchestrator calls instead of using the orchestrator's gzipping `--download` path. |
| [0004](./adr/0004-mock-layer-for-offline-dev.md) | **A `mocks/` directory fakes every external system** so the tool runs end-to-end on a developer laptop. |
| [0005](./adr/0005-scr-modification-policy.md) | **The `scr/` orchestrators get a loosened modification policy** — obvious bug fixes and de-duplication are allowed once the mock layer lands, with required validation. |

---

## 5. Repository layout (target)

```
/                                          # repo root
├── CONTEXT.md                             # domain glossary
├── README.md                              # rewritten at v1.0 to describe Dispatch
├── docs/
│   ├── plan.md                            # this file
│   ├── adr/                               # ADRs 0001–0005
│   └── agents/                            # existing agent skill docs
├── scr/                                   # orchestrators (frozen API)
│   ├── README.md                          # NEW — "stable; see ADR-0005"
│   ├── Query_Impala_Parametrized.py
│   ├── download_to_csv.py
│   ├── monthly_query_processor.py
│   └── _common.py                         # NEW (post-ADR-0005) — shared helpers
├── dispatch/                              # NEW — the TUI Python package
│   ├── __init__.py
│   ├── __main__.py                        # entry point: `python -m dispatch`
│   ├── app.py                             # Textual App
│   ├── process.py                         # SOLE sanctioned subprocess entry point
│   ├── runner.py                          # the runner script (spawned via nohup+setsid)
│   ├── manifest.py                        # Job manifest schema + I/O
│   ├── jobs.py                            # Job listing, state queries, concurrency cap
│   ├── kerberos.py                        # klist parsing, suspend-and-run kinit
│   ├── sql.py                             # template detection, SQL preview, partition preview
│   ├── impala.py                          # SHOW TABLES / DESCRIBE / DROP for the browser
│   ├── config.py                          # ~/.dispatch/config.json read/write
│   ├── version.py                         # __version__ constant; compared to deployed VERSION
│   └── screens/
│       ├── dashboard.py
│       ├── new_job.py
│       ├── job_detail.py
│       ├── history.py
│       └── browser.py
├── mocks/                                 # NEW — see ADR-0004
│   ├── bin/
│   ├── smtpd.py
│   ├── scenarios/
│   └── dev-env.sh
├── vendor/                                # NEW — pinned wheels for offline install
├── requirements.txt                       # NEW — pinned deps
├── pyproject.toml                         # NEW — defines the `dispatch` console script
├── install.sh                             # NEW — per-user installer; idempotent
└── VERSION                                # NEW — single source of truth for version string
```

The legacy GUI files (`run_query.ps1`, `run_query_engine.bat`) are deleted at
v1.0.

---

## 6. Per-user data directory

```
/ads_storage/<user>/.dispatch/
├── config.json                # email; future per-user defaults
├── installed_version          # written by install.sh; compared to repo VERSION
├── venv/                      # the per-user venv
└── jobs/
    └── <jobid>/               # per-Job directory
        ├── manifest.json      # see schema below
        ├── run.log            # nohup target — stdout+stderr of orchestrator(s)
        ├── run.pid            # PID = process group ID (for killpg cancel)
        └── job.sql            # snapshot of submitted SQL at launch time
```

`<jobid>` format: `<UTC ISO-8601 compact>_<6-char-base32-random>` — e.g.
`20260509T164500Z_a1b2c3`.

### Manifest schema

```json
{
  "schema_version": 1,
  "id": "20260509T164500Z_a1b2c3",
  "tool": "dispatch",
  "user": "e123456",
  "source": {
    "type": "SqlFile",
    "sql_path_at_launch": "/home/e123456/projects/q3/foo.sql"
  },
  "destination": {
    "type": "Table+Csv",
    "schema": "dw_settle",
    "table_name": "q3_load",
    "csv_path": "/home/e123456/projects/q3/q3_load.csv"
  },
  "params": {
    "to_email": "team@mastercard.com",
    "subject": "Q3 settlement load"
  },
  "orchestrator_calls": [
    {"script": "Query_Impala_Parametrized.py", "argv": ["..."]},
    {"script": "download_to_csv.py", "argv": ["..."]}
  ],
  "state": "Running",
  "pid": 12345,
  "started_at": "2026-05-09T16:45:00Z",
  "finished_at": null,
  "exit_code": null
}
```

---

## 7. The runner script (`dispatch/runner.py`)

A small stdlib-only Python script the TUI launches via `nohup` + `setsid`.

```python
# Pseudocode — dispatch/runner.py
def main(jobid: str) -> None:
    job_dir = Path(os.environ.get("DISPATCH_DATA_ROOT",
                                  f"/ads_storage/{os.environ['USER']}/.dispatch")) / "jobs" / jobid
    manifest = Manifest.load(job_dir / "manifest.json")
    log = open(job_dir / "run.log", "ab", buffering=0)
    (job_dir / "run.pid").write_text(str(os.getpid()))

    manifest.update(state="Running", started_at=now_utc(), pid=os.getpid())

    try:
        for call in manifest["orchestrator_calls"]:
            rc = subprocess.run(call["argv"], stdout=log, stderr=log).returncode
            if rc != 0:
                manifest.update(state="Failed", exit_code=rc, finished_at=now_utc())
                return
        manifest.update(state="Succeeded", exit_code=0, finished_at=now_utc())
    except Exception as e:
        log.write(f"\n[runner] Unhandled error: {e}\n".encode())
        manifest.update(state="Failed", exit_code=-1, finished_at=now_utc())
```

The runner is `setsid`-spawned by the TUI via `dispatch/process.py`, so its
PID is its process group leader. Cancel from the TUI is
`os.killpg(manifest["pid"], signal.SIGTERM)`.

---

## 8. The TUI

### Navigation

Three top-level tabs plus a modal-style "New Job" wizard:

- **Dashboard** — Active Jobs (max 2) and Recently Finished (last 7 days).
- **History** — Jobs older than 7 days. Searchable by table name and date.
- **Browser** — Impala metadata: list/describe/drop tables in a schema.

Persistent header shows `Kerberos: <ttl>` and a "deployed version vs.
installed version" warning when they differ.

### Dashboard wireframe

```
┌─ Dispatch ─────────────────────────────────── Kerberos: 7h 32m ─┐
│  Active Jobs (1 / 2)                                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ID            Source      Destination     State    Elapsed │ │
│  │ 2026…_a1b2c3  SqlFile     Table + Csv     Running     3m   │ │
│  └────────────────────────────────────────────────────────────┘ │
│  Recently Finished                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 2026…_99fa01  SqlTemplate Table         Succeeded     42m   │ │
│  │ 2026…_77bd02  SqlFile     Csv           Failed        18s   │ │
│  └────────────────────────────────────────────────────────────┘ │
│ [N]ew Job [A]ttach [C]ancel [V]iew Logs [H]istory [B]rowse [Q]  │
└─────────────────────────────────────────────────────────────────┘
```

### New Job wireframe

```
┌─ New Job ──────────────────────────────────── Kerberos: 7h 32m ─┐
│  SQL File:     [foo.sql                                      ▼] │
│                Auto-detected: SqlFile (no {date_*} markers)     │
│                [E]dit in $EDITOR    [Shift-N] New blank         │
│                                                                 │
│  Source:       (•) SqlFile  ( ) SqlTemplate  ( ) ExistingTable  │
│  Destination:  ( ) Table    (•) Csv          ( ) Table + Csv    │
│                                                                 │
│  Schema:       [dw_settle                                     ] │
│  Table name:   [q3_settle_load                                ] │
│  Email:        [team@mastercard.com                           ] │
│  Subject:      [Q3 settlement load                            ] │
│                                                                 │
│  Date range:   (hidden — only shown for SqlTemplate)            │
│                                                                 │
│  [P]review SQL  [L]aunch  [Esc] Back                            │
└─────────────────────────────────────────────────────────────────┘
```

Behaviour:

- The SQL File picker defaults to `*.sql` in the launch-time `$PWD`.
- Source is **auto-detected** from the file: presence of both
  `{date_inicio}` and `{date_fim}` → `SqlTemplate`; absence → `SqlFile`. A
  mismatch with the user's explicit pick produces a soft warning with a
  one-key flip.
- Hard-refused launches: missing Kerberos ticket; ticket TTL < 5 minutes;
  user already has 2 Running Jobs; illegal `(Source, Destination)` cell;
  `SqlTemplate` source without both placeholders.
- Soft warnings: ticket TTL < 1 hour; CWD not writable for `Csv`
  destinations.
- `[P]review SQL` shows the wrapped DDL (for `Table` destinations) or the
  resolved monthly partitions (for `SqlTemplate`).

### Job Detail wireframe (the reattached live tail)

```
┌─ Job 20260509T164500Z_a1b2c3 ──────────────── Kerberos: 7h 28m ─┐
│  Source: SqlFile (foo.sql)     Destination: Table + Csv         │
│  State:  Running               Started: 16:45:02 (3m 14s ago)   │
│  Table:  dw_settle.q3_settle_load                               │
│  CSV:    /home/e123456/projects/q3/q3_settle_load.csv           │
│  ┌─ run.log (live) ───────────────────────────────────────────┐ │
│  │ 16:45:02 INFO  Executing query on adhoc_fast               │ │
│  │ 16:45:35 WARN  adhoc_fast returned QUEUE_FULL              │ │
│  │ 16:45:35 INFO  Trying acs_small                            │ │
│  │ 16:46:08 INFO  Query accepted on acs_small                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│ [C]ancel Job  [B]ack                                            │
└─────────────────────────────────────────────────────────────────┘
```

Implementation: `RichLog` widget bound to a tailing `open(run.log,
"rb")`-style coroutine. Bounded memory regardless of total log size.

### Browser wireframe

```
┌─ Browse Impala Metadata ────────────────────── Kerberos: 7h 28m ┐
│  Schema: [dw_settle             ▼]   Filter: [your_*          ] │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Table                          Updated      Size  Rows     │ │
│  │ your_test_table                2026-05-08   ?     ?        │ │
│  │ your_q3_load                   2026-05-07   ?     ?        │ │
│  └────────────────────────────────────────────────────────────┘ │
│ [Enter] Describe  [E]xport to CSV  [D]rop  [B]ack               │
└─────────────────────────────────────────────────────────────────┘
```

`Size`/`Rows` populate lazily via `SHOW TABLE STATS` only when a row is
selected, to avoid hammering the cluster on schema browse.

---

## 9. Install flow (`install.sh`)

Per-user, idempotent, re-runnable for upgrades:

1. **Verify environment**: Python 3.10 at the existing
   `/sys_apps_01/python/python310/bin/python3.10`; `klist` and
   `impala-shell` present; `/ads_storage/$USER/` writable.
2. **Create venv** at `/ads_storage/$USER/.dispatch/venv/`.
3. **Install vendored wheels**:
   `pip install --no-index --find-links=/ads_storage/dispatch/vendor/ \
   -r /ads_storage/dispatch/requirements.txt`
4. **Install the `dispatch` shortcut**: symlink
   `~/.local/bin/dispatch → /ads_storage/$USER/.dispatch/venv/bin/dispatch`.
   If `~/.local/bin` is not on `$PATH`, append
   `alias dispatch='...'` to `~/.bashrc` (and `~/.zshrc` if it exists),
   detected by the user's actual `$SHELL`.
5. **Create skeleton**: `~/.dispatch/jobs/`.
6. **First-run only**: prompt for email; write `~/.dispatch/config.json`.
   No schema prompt — schema changes per Job.
7. **Record installed version**: write `~/.dispatch/installed_version` from
   the repo's `VERSION` file.
8. **Print "open a new shell and run `dispatch`"**.

Re-run = upgrade in place. `~/.dispatch/jobs/` and `config.json` are never
touched on re-run.

---

## 10. Mock layer

See [ADR-0004](./adr/0004-mock-layer-for-offline-dev.md). To enter dev mode
on a non-Hadoop machine:

```bash
source mocks/dev-env.sh   # exports DISPATCH_DATA_ROOT, prepends mocks/bin to PATH,
                          # sets MAILHOST, starts SMTP catcher, prints banner
dispatch
```

Scenarios live in `mocks/scenarios/<name>.json`; switch with
`export DISPATCH_MOCK_SCENARIO=memory_exceeded`. Captured emails appear as
`.eml` files in `mocks/sent_emails/` (gitignored).

---

## 11. Migration

At v1.0 ship:

- **Hard delete** `run_query.ps1` and `run_query_engine.bat`.
- **Rewrite** `README.md` to describe Dispatch (the existing README is
  Windows-GUI-centric).
- **Rename deploy path** on the edge node from
  `/ads_storage/hadoop_query_launcher/` to `/ads_storage/dispatch/`. The
  hardcoded path in `Query_Impala_Parametrized.export_table_to_csv` is
  externalised to `DISPATCH_SCR_DIR` per ADR-0005 as part of the same
  change.
- **No coexistence period.** Existing PowerShell users move directly to
  `dispatch` on the edge node.

---

## 12. Implementation milestones

Even though every primitive is in v1.0 (no "phase 2"), the PR sequence
matters for safe, reviewable, mock-validated progress.

| # | PR | Lands |
|---|---|---|
| 1 | `mocks/` substrate | ADR-0004 in code; CI can run end-to-end against fakes |
| 2 | `dispatch/` package skeleton + `pyproject.toml` + `requirements.txt` + `vendor/` | `python -m dispatch` opens an empty Textual app on the dev VM |
| 3 | Manifest schema + runner script + `dispatch/process.py` | ADR-0001 in code; runner can be smoke-tested against mock scenarios |
| 4 | New Job wizard with Source × Destination logic, `$EDITOR` shell-out, template auto-detect, Kerberos pre-flight | First end-to-end "I can launch a Job" PR |
| 5 | Dashboard with active/finished tables, attach to live tail, cancel | First "I can supervise a Job" PR |
| 6 | History view with 7-day collapse | Closes the Job-lifecycle category |
| 7 | Impala metadata browser | `SHOW TABLES` / `DESCRIBE` / `DROP` |
| 8 | SQL preview + monthly partition preview | Pre-launch trust-builder primitives |
| 9 | `install.sh` + `VERSION` file + version-mismatch banner | Distribution path |
| 10 | `scr/` de-duplication + `_common.py` + path externalisation | ADR-0005 in code |
| 11 | Hard delete legacy GUI; README rewrite | v1.0 ship |

PRs 1–3 are blocking dependencies for everything after. Beyond that, 4–8
can be parallelised by different contributors. PR 10 cannot land before
PR 1 (ADR-0005 requires the mock layer).

---

## 13. Known risks

| Risk | Mitigation |
|---|---|
| Textual on a corporate jumphost may glitch on terminal-feature negotiation | First Edge Node smoke-test at PR 2; fall back to `urwid` is documented in ADR-0002 if needed |
| Kerberos `klist` not on `$PATH` on some hardened nodes | Graceful degradation: pre-flight skipped, orchestrator's `AUTH_ERROR` path catches it; warning written to `~/.dispatch/dispatch.log` |
| User runs `dispatch` from a CWD they can't write to | Soft warning at New Job time for `Csv` destinations; orchestrator surfaces filesystem error if user proceeds |
| Concurrent re-installs by the same user race on `venv/` | `install.sh` takes a lockfile at `~/.dispatch/install.lock` |
| `scr/` modifications regress production behaviour despite mock validation | ADR-0005's required process — two reviewers, one with prod-run experience, side-by-side log captures |
| Mock layer drifts from real `impala-shell` argv | Treated as integration bug; argv contract documented in `mocks/bin/impala-shell` source comment, paired with the orchestrators' actual invocations |

---

## 14. Out of scope for v1.0

Recorded so they don't get re-litigated:

- Auto-queueing of a 3rd Job when 2 slots are full (hard refuse only).
- Cross-user Job visibility.
- Cluster / queue health dashboard.
- Mid-Job Kerberos auto-renewal.
- A staging-cluster integration test environment.
- Resume-from-failure for partially-completed `Table + Csv` Jobs.
