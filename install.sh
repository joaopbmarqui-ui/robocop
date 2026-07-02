#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)
USER_NAME=${USER:-$(id -un)}
DATA_ROOT=${DISPATCH_DATA_ROOT:-/ads_storage/$USER_NAME}
DISPATCH_HOME="$DATA_ROOT/.dispatch"
BUNDLE_DIR=${EDGE_DEPLOY_BUNDLE_DIR:-/ads_storage/$USER/.edge-deploy/bundles/robocop/current}
WHEEL_DIR="$BUNDLE_DIR/wheels"
REQUIREMENTS_FILE="$BUNDLE_DIR/requirements/requirements.txt"
PYTHON_BIN=${EDGE_DEPLOY_PYTHON_BIN:-${DISPATCH_PYTHON_BIN:-}}
if [ -z "$PYTHON_BIN" ]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3.11)
  elif command -v python3.10 >/dev/null 2>&1; then
    PYTHON_BIN=$(command -v python3.10)
  else
    PYTHON_BIN=/sys_apps_01/python/python310/bin/python3.10
  fi
fi

if [ ! -d "$DATA_ROOT" ] || [ ! -w "$DATA_ROOT" ]; then
  echo "$DATA_ROOT must exist and be writable" >&2
  exit 1
fi

mkdir -p "$DISPATCH_HOME/jobs"
chmod 700 "$DISPATCH_HOME" "$DISPATCH_HOME/jobs"

LOCK_FILE="$DISPATCH_HOME/install.lock"
# exec 9>"$LOCK_FILE"
# flock 9

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python 3.10 not found at $PYTHON_BIN" >&2
  echo "Set DISPATCH_PYTHON_BIN for dev-mode validation if needed." >&2
  exit 1
fi

command -v klist >/dev/null 2>&1 || { echo "klist not found on PATH" >&2; exit 1; }
command -v impala-shell >/dev/null 2>&1 || { echo "impala-shell not found on PATH" >&2; exit 1; }

"$PYTHON_BIN" -m venv "$DISPATCH_HOME/venv"
if [ ! -f "$BUNDLE_DIR/manifest.json" ] || [ ! -f "$REQUIREMENTS_FILE" ]; then
  echo "Verified dependency bundle not found: $BUNDLE_DIR" >&2
  echo "Run the edge-deploy dependency delivery phase before installing." >&2
  exit 1
fi
"$DISPATCH_HOME/venv/bin/pip" install --no-index --find-links="$WHEEL_DIR" -r "$REQUIREMENTS_FILE"
# "$DISPATCH_HOME/venv/bin/pip" install --no-deps -e "$ROOT_DIR"

LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"
cat > "$LOCAL_BIN/dispatch" <<EOF
#!/bin/bash
export PYTHONPATH="$ROOT_DIR"
exec "$DISPATCH_HOME/venv/bin/python" -m dispatch "\$@"
EOF
chmod +x "$LOCAL_BIN/dispatch"

SHELL_RC="$HOME/.bashrc"
[ "${SHELL:-}" ] && [ "$(basename "$SHELL")" = "zsh" ] && [ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
case ":$PATH:" in
  *":$LOCAL_BIN:"*) ;;
  *)
    if ! grep -F "$PATH_LINE" "$SHELL_RC" >/dev/null 2>&1; then
      printf '\n# Dispatch command\n%s\n' "$PATH_LINE" >>"$SHELL_RC"
    fi
    ;;
esac

CONFIG="$DISPATCH_HOME/config.json"
if [ ! -f "$CONFIG" ]; then
  EMAIL=${EDGE_DEPLOY_EMAIL:-${DISPATCH_EMAIL:-}}
  if [ -z "$EMAIL" ]; then
    printf "Email: "
    read -r EMAIL
  fi
  CONFIG_TMP="$CONFIG.tmp.$$"
  trap 'rm -f "$CONFIG_TMP"' 0
  trap 'exit 1' 1 2 15
  "$PYTHON_BIN" - "$CONFIG_TMP" "$EMAIL" <<'PY'
import json
import sys

config_path, email = sys.argv[1:]
with open(config_path, "w", encoding="utf-8", newline="\n") as config_file:
    json.dump({"form_defaults": {"email": email}}, config_file, indent=2)
    config_file.write("\n")
PY
  mv "$CONFIG_TMP" "$CONFIG"
  trap - 0 1 2 15
fi

cp "$ROOT_DIR/VERSION" "$DISPATCH_HOME/installed_version"
echo
echo "Dispatch installed."
case ":$PATH:" in
  *":$LOCAL_BIN:"*)
    echo "The dispatch command is available in this shell."
    ;;
  *)
    echo "To use dispatch in this shell now:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "New shells will pick this up automatically from $SHELL_RC."
    ;;
esac
echo "Then cd to your SQL files and run: dispatch"
