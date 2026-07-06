#!/usr/bin/env bash
# Reproduce the PR #4 Browse table-search clarity demo video locally.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# Mock Hadoop/Kerberos layer required by DispatchApp startup.
# shellcheck source=/dev/null
source mocks/dev-env.sh

exec "${DISPATCH_PYTHON_BIN:-/workspace/.venv/bin/python}" \
  demos/pr4-browse-table-search-clarity/capture_demo.py
