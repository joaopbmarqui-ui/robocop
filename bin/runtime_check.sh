# Shared validation of the active Dispatch runtime. POSIX sh; sourced by
# bin/dispatch and onboard.sh.
#
# dispatch_active_runtime <root-dir>
#   Prints the physical path of the validated active runtime on stdout, or
#   prints an actionable error to stderr and returns non-zero. <root-dir> must
#   be a physical path (resolved with pwd -P) so it compares equal to the
#   readlink -f result even when the repository lives on a symlinked mount.
dispatch_active_runtime() {
  _root=$1
  _current="$_root/.venv/current"
  if [ ! -L "$_current" ]; then
    echo "Dispatch shared runtime is not active at $_current." >&2
    echo "Ask the Release Operator to run $_root/install.sh." >&2
    return 1
  fi
  _runtime=$(readlink -f "$_current" 2>/dev/null || true)
  if [ -z "$_runtime" ] || [ ! -d "$_runtime" ] || [ ! -f "$_runtime/.complete.json" ]; then
    echo "Dispatch shared runtime is invalid at $_current." >&2
    echo "Ask the Release Operator to reactivate a completed runtime." >&2
    return 1
  fi
  case "$_runtime" in
    "$_root/.venv/releases/"*) ;;
    *)
      echo "Dispatch shared runtime resolves outside the release root: $_runtime." >&2
      return 1
      ;;
  esac
  _digest=$(basename "$_runtime")
  if ! grep -Eq '"bundle_digest"[[:space:]]*:[[:space:]]*"'"$_digest"'"' "$_runtime/.complete.json" ||
     ! grep -Eq '"pip_check"[[:space:]]*:[[:space:]]*"passed"' "$_runtime/.complete.json"; then
    echo "Dispatch shared runtime completion metadata is corrupt: $_runtime/.complete.json." >&2
    return 1
  fi
  if [ ! -x "$_runtime/bin/python" ]; then
    echo "Dispatch shared runtime has no executable Python at $_runtime/bin/python." >&2
    return 1
  fi
  printf '%s\n' "$_runtime"
}
