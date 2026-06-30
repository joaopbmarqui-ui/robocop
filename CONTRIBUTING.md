# Contributing to Dispatch

This is the shortest safe path for making a change.

## 1. Set up

```bash
cd D:\Projects\robocop
python -m pip install -e ".[dev]"
```

For local TUI runs, always source the mock environment in the same shell:

```bash
source mocks/dev-env.sh
DISPATCH_EMAIL=you@example.com DISPATCH_PYTHON_BIN=$(command -v python3) ./install.sh
```

## 2. Make a change

Start from `main` unless the user asks for a branch.

```bash
git status --short --branch
git branch -vv
```

Use focused tests for the files you touched.

For TUI work, use `.agents/skills/dispatch-textual-tui/SKILL.md`.

For `scr/` work, read `docs/adr/0005-scr-modification-policy.md` first.

## 3. Validate locally

Fast checks:

```bash
python -m compileall dispatch scr
python -m dispatch --help
```

Mock smoke:

```bash
source mocks/dev-env.sh
DISPATCH_MOCK_SCENARIO=happy_path python -m dispatch
```

Full local gate:

```powershell
.\tools\dev\local_check.ps1
```

## 4. Commit

```bash
git diff
git add <files>
git commit -m "Describe the change"
```

Do not commit generated reports, screens, logs, deploy zips, credentials,
passcodes, Kerberos passwords, or ad hoc server files.

## 5. Release

Normal releases happen from `edge-deploy-core`, not from this repo:

```powershell
cd D:\Projects\edge-deploy-core
py -m edge_deploy release --tool robocop --smoke standard
```

Use repo-local deployment tools only for bootstrap, recovery, or diagnosis.
