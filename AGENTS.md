# Dispatch Agent Guide

Dispatch is a server-side Textual TUI for launching and supervising Impala
jobs. Product code lives in `dispatch/`; production orchestrators live in
`scr/`; local infrastructure substitutes live in `mocks/`.

Follow [CONTRIBUTING.md](CONTRIBUTING.md). Work from current GitHub `main`, use a
short-lived branch, run `python -m pytest`, and finish with a GitHub pull
request.

Agents may create branches, commit, push a branch, and open a pull request when
requested. Agents must not merge, change branch protection, create release
tags, push Bitbucket, or deploy without explicit Release Operator instruction.

Do not reintroduce the legacy Windows GUI. Keep `scr/` standard-library-only
and follow [ADR-0005](docs/adr/0005-scr-modification-policy.md). Do not commit
generated artifacts or secrets.

For Textual work, use `.agents/skills/dispatch-textual-tui/SKILL.md`. Release
Operators use [docs/release-workflow.md](docs/release-workflow.md).
