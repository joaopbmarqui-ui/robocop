Correct. For **real production-server validation**, the best setup is:

```text
agent → SSH → remote tmux session → real dispatch TUI → real Edge Node tools
```

Mocks should only be for local dev. The repo itself says Dispatch runs on the Hadoop Edge Node, users SSH there, run `dispatch`, and jobs must survive disconnects.  It also explicitly says production merge may require smoke-testing over the corporate SSH chain, real `/ads_storage`, Kerberos, real `impala-shell`, and deployment to `/ads_storage/dispatch/`. 

### Recommended production setup

Create a **remote tmux harness** with four operations:

```text
start_session
send_keys
capture_screen
stop_session
```

The agent should not use plain `subprocess` alone, because Dispatch is a real Textual TUI, not a normal stdin/stdout CLI. tmux gives you persistence, screen capture, and the ability for you to attach manually.

### Minimal commands

From your local/headless controller:

```bash
export HOST="your-user@edge-node"
export REPO="/ads_storage/dispatch"   # or deployed robocop path
export SESSION="robocop-prod-test"

ssh "$HOST" "tmux kill-session -t $SESSION 2>/dev/null || true"

ssh "$HOST" "tmux new-session -d -s $SESSION -x 120 -y 40 'cd $REPO && bash'"

ssh "$HOST" "tmux send-keys -t $SESSION 'python -m compileall dispatch scr' Enter"
ssh "$HOST" "tmux capture-pane -t $SESSION -p -S -200"
```

Launch real TUI:

```bash
ssh "$HOST" "tmux send-keys -t $SESSION 'cd /path/to/sql/files && dispatch' Enter"
ssh "$HOST" "tmux capture-pane -t $SESSION -p -S -200"
```

Attach yourself:

```bash
ssh -t "$HOST" "tmux attach -t $SESSION"
```

### What the agent should test in prod

Use three test levels.

**Level 1 — safe production smoke**

No job launch:

```text
- SSH works
- tmux starts at 120x40
- dispatch opens
- dashboard renders
- Kerberos status appears
- navigation works
- SQL browser opens
- history opens
- preview screen opens
- quit works cleanly
```

**Level 2 — real environment checks**

Still no destructive launch:

```text
- install.sh works against real /ads_storage user path
- dispatch shortcut resolves correctly
- klist is detected
- impala-shell is on PATH
- current working directory is captured correctly
- Textual layout works over corporate SSH
```

The repo requires `klist`, `impala-shell`, Python 3.10, writable `/ads_storage/<user>`, and an idempotent install path. 

**Level 3 — controlled real job**

Only with a dedicated scratch query/table:

```sql
SELECT 1 AS smoke_test_value
```

Use a table/output prefix like:

```text
dispatch_smoke_${USER}_YYYYMMDD_HHMMSS
```

The agent should be allowed to press **Launch** only when:

```text
- target schema is explicitly scratch/writable
- SQL file is known and tiny
- destination table/output name starts with dispatch_smoke_
- Kerberos TTL is healthy
- no more than the allowed running-job cap is active
```

The app’s invariants include refusing missing/low Kerberos tickets and more than two simultaneous running jobs. 

### Best agent tool design

I’d add a project-local tool/script like:

```text
tools/prod_tui/
  robocop_tmux.py
  README.md
```

With commands:

```bash
python tools/prod_tui/robocop_tmux.py start
python tools/prod_tui/robocop_tmux.py send "dispatch"
python tools/prod_tui/robocop_tmux.py keys tab enter
python tools/prod_tui/robocop_tmux.py capture
python tools/prod_tui/robocop_tmux.py attach
python tools/prod_tui/robocop_tmux.py stop
```

The agent loop becomes:

```text
capture screen
reason about current UI
send key/action
capture again
assert expected visible state
```

### Safety rule I’d enforce

For production, split actions into:

```text
SAFE: navigate, preview, capture, inspect logs/history, run --help, compileall
CONTROLLED: launch smoke query with dispatch_smoke_ prefix
BLOCKED: drop tables, run arbitrary SQL, modify scr/, delete files, launch unknown user SQL
```

This is the right tradeoff: **tmux is the production TUI driver**, while `pytest/Textual pilot` remains useful only for deterministic non-prod regression tests. For your requirement, the real acceptance harness should be SSH + tmux + real Edge Node.
