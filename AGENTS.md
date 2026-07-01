# Dispatch Agent Guide

Dispatch is a server-side Textual TUI for launching and supervising Impala jobs
from a Hadoop Edge Node.

Main surfaces:

- `dispatch/`: TUI, job model, manifest logic, detached runner
- `scr/`: production Impala orchestrators
- `mocks/`: local Hadoop/Kerberos/SMTP/Impala substitutes
- `tools/prod_tui/`: production SSH/tmux validation harness

## Non-negotiable rules

- Do not reintroduce the legacy Windows GUI direction.
- Keep `scr/` standard-library-only unless the user explicitly approves a
  production dependency change.
- Keep `scr/` edits narrow and follow `docs/adr/0005-scr-modification-policy.md`.
- Do not commit generated reports, screens, logs, deploy zips, credentials,
  RSA passcodes, or Kerberos secrets.
- Do not push to remotes unless the user explicitly asks.

## Local development

Use [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor runway.

Core loop:

```bash
source mocks/dev-env.sh
DISPATCH_EMAIL=you@example.com DISPATCH_PYTHON_BIN=$(command -v python3) ./install.sh
DISPATCH_MOCK_SCENARIO=happy_path python -m dispatch
```

Validation:

```bash
python -m compileall dispatch scr
python -m pytest tests tools/prod_tui/tests -q
python -m dispatch --help
```

## Project-specific skills

For Textual/UI work, read:

```text
.agents/skills/dispatch-textual-tui/SKILL.md
```

For release, recovery, Edge Node diagnostics, or shared
`/ads_storage/dispatch` permission fixes, read:

```text
.agents/skills/dispatch-edge-deploy/SKILL.md
```

## Release workflow

Default releases are orchestrated by the installed `edge-deploy-core` package:

```powershell
py -m edge_deploy release --tool robocop --smoke standard
```

Repo-local commands such as `tools.prod_tui deploy`, `update.sh`, and tmux/SSH
manual operation are bootstrap, recovery, or diagnosis tools only.

## Where to look

- Product/user docs: [README.md](README.md)
- Contributor path: [CONTRIBUTING.md](CONTRIBUTING.md)
- Release path: [docs/development-workflow.md](docs/development-workflow.md)
- Architecture decisions: [docs/adr](docs/adr)
- Production testing: [docs/production_testing.md](docs/production_testing.md)
