"""Regression checks for the Edge Node operating-model deployment contract."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_update_script_uses_reset_hard_and_preserves_untracked_runtime_state() -> None:
    update = _read("update.sh")

    assert "git fetch --prune" in update
    assert "git reset --hard" in update
    assert 'chmod 755 "$ROOT_DIR"' in update
    assert 'chmod -R a+rX "$ROOT_DIR"' in update
    assert "git clean" not in update


def test_update_script_is_tracked_executable() -> None:
    result = subprocess.run(
        ["git", "ls-files", "-s", "--", "update.sh"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.startswith("100755 "), result.stdout


def test_update_script_has_valid_posix_shell_syntax() -> None:
    if shutil.which("sh") is None:
        return

    subprocess.run(["sh", "-n", "update.sh"], cwd=ROOT, check=True)


def test_active_operator_docs_prefer_update_sh_over_pull_based_sync() -> None:
    docs = [
        "docs/development-workflow.md",
        "docs/edge-node-first-time-setup.md",
        "docs/edge-node-tui-operating-model.md",
        "docs/production_testing.md",
        "tools/prod_tui/README.md",
    ]

    for doc in docs:
        text = _read(doc)
        assert "update.sh" in text, doc
        assert "git pull --ff-only" not in text, doc


def test_deployment_remote_docs_use_snapshot_publish_discipline() -> None:
    workflow = _read("docs/development-workflow.md")
    status_script = _read("tools/dev/git_sync_status.ps1")
    publish_script = _read("tools/dev/publish_dispatch_snapshot.ps1")

    assert "operator-authored snapshot commit" in workflow
    assert (
        ".\\tools\\dev\\publish_dispatch_snapshot.ps1 -ReviewedCommit <reviewed-robocop-commit> -RunLocalCheck"
        in workflow
    )
    assert "git switch -c deploy/dispatch-snapshot <reviewed-robocop-commit>" in workflow
    assert "git reset --soft bitbucket/main" in workflow
    assert "git push bitbucket HEAD:main" in workflow
    assert "Do not run a casual `git push -u bitbucket HEAD`" in workflow
    assert "publish_dispatch_snapshot.ps1" in status_script
    assert "snapshot flow in docs/development-workflow.md" not in status_script
    assert "git push -u $Remote HEAD" not in status_script
    assert "[string]$ReviewedCommit" in publish_script
    assert "[switch]$RunLocalCheck" in publish_script
    assert "[switch]$LocalCheckPassed" in publish_script
    assert "[switch]$DryRun" in publish_script
    assert "switch -C $TempBranch $resolvedReviewedCommit" in publish_script
    assert "reset --soft $remoteRef" in publish_script
    assert "HEAD:$Branch" in publish_script


def test_artifact_and_line_ending_hygiene_matches_operating_model() -> None:
    attributes = _read(".gitattributes")
    ignore = _read(".gitignore")

    assert "*.py text eol=lf" in attributes
    assert "*.sh text eol=lf" in attributes
    assert "*.zip" in ignore
    assert "tools/prod_tui/screens/" in ignore
    assert "tools/prod_tui/reports/" in ignore
    assert "tools/prod_tui/logs/" in ignore


def test_zip_deploy_scripts_include_the_shared_tree_updater() -> None:
    deploy_one = _read("deploy_and_install.ps1")
    deploy_both = _read("deploy_nodes_03_04.ps1")

    assert "'update.sh'" in deploy_one
    assert '$UpdateScript = "update.sh"' in deploy_one
    assert "chmod +x $SetupScript $UpdateScript" in deploy_one
    assert '$UpdateScript = "update.sh"' in deploy_both
    assert "chmod +x $SetupScript $UpdateScript" in deploy_both
