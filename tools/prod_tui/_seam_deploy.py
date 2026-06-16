"""One-shot helper to fetch / compare / deploy dispatch/app.py over the
authenticated tmux pane. Temporary tooling for the production smoke harness."""
from __future__ import annotations

import base64
import hashlib
import re
import sys
from pathlib import Path

from tools.prod_tui.robocop_tmux import driver_from_config_path, DEFAULT_CONFIG_PATH

REMOTE = "/ads_storage/dispatch/dispatch/app.py"
LOCAL = Path("dispatch/app.py")
REMOTE_COPY = Path("tools/prod_tui/_remote_app.py")

# Local source root -> remote deployed root. The repo is deployed at
# /ads_storage/dispatch, so the package lives at /ads_storage/dispatch/dispatch.
SYNC_ROOTS = (
    ("dispatch", "/ads_storage/dispatch/dispatch"),
    ("scr", "/ads_storage/dispatch/scr"),
)


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _remote_md5s(d, remote_root: str) -> dict[str, str]:
    """Return {relpath: md5} for every *.py under a remote root in one round-trip."""
    out, _ = d.run_remote(
        f"find {remote_root} -name '*.py' -not -path '*/__pycache__/*' "
        f"-exec md5sum {{}} +",
        timeout=90,
    )
    result: dict[str, str] = {}
    prefix = remote_root.rstrip("/") + "/"
    for line in out.splitlines():
        m = re.match(r"([0-9a-f]{32})\s+(\S.*)$", line.strip())
        if not m:
            continue
        path = m.group(2)
        if path.startswith(prefix):
            result[path[len(prefix):]] = m.group(1)
    return result


def _scan() -> list[tuple[str, str, str, str, str]]:
    """Compare local vs remote for all sync roots.

    Returns rows of (status, local_root, relpath, local_md5, remote_md5).
    """
    d = _driver()
    rows: list[tuple[str, str, str, str, str]] = []
    for local_root, remote_root in SYNC_ROOTS:
        lroot = Path(local_root)
        if not lroot.exists():
            continue
        remote = _remote_md5s(d, remote_root)
        local_rels = {p.relative_to(lroot).as_posix() for p in lroot.rglob("*.py")
                      if "__pycache__" not in p.parts}
        for rel in sorted(local_rels):
            lmd5 = _md5(lroot / rel)
            rmd5 = remote.get(rel, "")
            if not rmd5:
                rows.append(("MISSING_REMOTE", local_root, rel, lmd5, ""))
            elif rmd5 != lmd5:
                rows.append(("DIFFER", local_root, rel, lmd5, rmd5))
            else:
                rows.append(("MATCH", local_root, rel, lmd5, rmd5))
        for rel in sorted(remote):
            if rel not in local_rels:
                rows.append(("MISSING_LOCAL", local_root, rel, "", remote[rel]))
    return rows


def verify() -> None:
    rows = _scan()
    drift = [r for r in rows if r[0] != "MATCH"]
    for status, root, rel, lmd5, rmd5 in rows:
        if status == "MATCH":
            continue
        print(f"[{status:14}] {root}/{rel}  local={lmd5[:8] or '--------'} remote={rmd5[:8] or '--------'}")
    matched = sum(1 for r in rows if r[0] == "MATCH")
    print(f"\nMATCH={matched}  DRIFT={len(drift)}  TOTAL={len(rows)}")
    if not drift:
        print("IN_SYNC")


def sync() -> None:
    """Redeploy drifted dispatch/ files. scr/ drift is reported but never
    auto-deployed (production-sensitive orchestrators)."""
    rows = _scan()
    for status, root, rel, lmd5, rmd5 in rows:
        if status == "MATCH":
            continue
        if root == "scr":
            print(f"[SKIP-SCR {status}] {root}/{rel} (deploy manually if intended)")
            continue
        if status == "MISSING_LOCAL":
            print(f"[SKIP {status}] {root}/{rel} (exists only on remote)")
            continue
        local_rel = f"{root}/{rel}"
        remote_path = f"{dict(SYNC_ROOTS)[root]}/{rel}"
        print(f"--- deploying {local_rel} -> {remote_path} ({status}) ---")
        deploy_file(local_rel, remote_path)
    print("\n--- re-verifying ---")
    verify()


def _driver():
    _cfg, d = driver_from_config_path(DEFAULT_CONFIG_PATH)
    return d


def fetch() -> None:
    d = _driver()
    out, code = d.run_remote(f"base64 {REMOTE} | tr -d '\\n'", timeout=30)
    if code != 0:
        print("FETCH FAILED", code)
        print(out[-500:])
        sys.exit(1)
    data = base64.b64decode("".join(out.split()))
    REMOTE_COPY.write_bytes(data)
    print("FETCHED", len(data), "bytes ->", REMOTE_COPY)


def deploy(src: Path) -> None:
    d = _driver()
    payload = src.read_bytes()
    encoded = base64.b64encode(payload).decode("ascii")
    # Back up the current remote file once.
    _, code = d.run_remote(f"cp -n {REMOTE} {REMOTE}.seam_bak", timeout=20)
    print("backup exit", code)
    chunk = 1000
    parts = [encoded[i:i + chunk] for i in range(0, len(encoded), chunk)]
    tmp = "/tmp/app_seam.b64"
    for idx, part in enumerate(parts):
        redir = ">" if idx == 0 else ">>"
        _, c = d.run_remote(f"printf %s '{part}' {redir} {tmp}", timeout=20)
        if c != 0:
            print("chunk", idx, "failed", c)
            sys.exit(1)
    _, c = d.run_remote(f"base64 -d {tmp} > {REMOTE}", timeout=20)
    print("decode exit", c)
    # Validate syntax and seam presence remotely.
    out, c = d.run_remote(
        f"python3 -c \"import ast,sys; ast.parse(open('{REMOTE}').read()); "
        f"print('SEAM' if 'DISPATCH_TEST_PREFILL' in open('{REMOTE}').read() else 'NOSEAM')\"",
        timeout=25,
    )
    print("validate exit", c)
    print(out[-300:])


def diag() -> None:
    d = _driver()
    py = "/ads_storage/e176097/.dispatch/venv/bin/python"
    out, code = d.run_remote(f"{py} -c 'import textual; print(textual.__version__)'", timeout=25)
    print("textual exit", code, "->", out.strip().splitlines()[-2] if out.strip().splitlines() else "")
    out, code = d.run_remote("md5sum /ads_storage/dispatch/dispatch/screens/new_job.py", timeout=20)
    import re
    m = re.search(r"([0-9a-f]{32})", out)
    print("new_job md5", m.group(1) if m else "NONE")


def diag2() -> None:
    d = _driver()
    py = "/ads_storage/e176097/.dispatch/venv/bin/python"
    out, _ = d.run_remote(f"{py} -m pip show textual 2>/dev/null | grep -i version", timeout=25)
    print("--- textual version ---")
    print(out)
    out, _ = d.run_remote(
        "grep -n -A 35 'def _apply_prefill' /ads_storage/dispatch/dispatch/screens/new_job.py",
        timeout=20,
    )
    print("--- remote _apply_prefill ---")
    print(out)


def whichmod() -> None:
    d = _driver()
    py = "/ads_storage/e176097/.dispatch/venv/bin/python"
    cmd = (
        f"PYTHONPATH=/ads_storage/dispatch {py} -c "
        "'import dispatch.screens.new_job as m; print(m.__file__); "
        "import inspect; src=inspect.getsource(m._apply_prefill) if hasattr(m,\"_apply_prefill\") else \"\"; "
        "print(\"HAS_PRESS\", \"_press_radio\" in open(m.__file__).read())'"
    )
    out, code = d.run_remote(cmd, timeout=30)
    print("exit", code)
    print(out[-700:])


def deploy_file(local_rel: str, remote_path: str) -> None:
    d = _driver()
    payload = Path(local_rel).read_bytes()
    encoded = base64.b64encode(payload).decode("ascii")
    d.run_remote(f"cp -n {remote_path} {remote_path}.seam_bak", timeout=20)
    chunk = 1000
    parts = [encoded[i:i + chunk] for i in range(0, len(encoded), chunk)]
    tmp = "/tmp/_deploy.b64"
    for idx, part in enumerate(parts):
        redir = ">" if idx == 0 else ">>"
        _, c = d.run_remote(f"printf %s '{part}' {redir} {tmp}", timeout=20)
        if c != 0:
            print("chunk", idx, "failed", c)
            sys.exit(1)
    _, c = d.run_remote(f"base64 -d {tmp} > {remote_path}", timeout=20)
    print("decode exit", c)
    out, c = d.run_remote(
        f"/ads_storage/e176097/.dispatch/venv/bin/python -c \"import ast; ast.parse(open('{remote_path}').read()); print('OK')\"",
        timeout=25,
    )
    print("validate exit", c, "->", out.strip().splitlines()[-2] if out.strip().splitlines() else "")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    if mode == "fetch":
        fetch()
    elif mode == "deploy":
        deploy(LOCAL)
    elif mode == "diag":
        diag()
    elif mode == "diag2":
        diag2()
    elif mode == "whichmod":
        whichmod()
    elif mode == "deploy-newjob":
        deploy_file("dispatch/screens/new_job.py", "/ads_storage/dispatch/dispatch/screens/new_job.py")
    elif mode == "deploy-manifest":
        deploy_file("dispatch/manifest.py", "/ads_storage/dispatch/dispatch/manifest.py")
    elif mode == "deploy-path":
        deploy_file(sys.argv[2], sys.argv[3])
    elif mode == "verify":
        verify()
    elif mode == "sync":
        sync()
    else:
        print(
            "usage: _seam_deploy.py "
            "[fetch|deploy|diag|deploy-newjob|deploy-manifest|deploy-path LOCAL REMOTE|verify|sync]"
        )
