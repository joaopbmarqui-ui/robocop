#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)
USER_NAME=${USER:-$(id -un)}
DATA_ROOT=${DISPATCH_DATA_ROOT:-/ads_storage/$USER_NAME}
DISPATCH_HOME="$DATA_ROOT/.dispatch"
CURRENT="$ROOT_DIR/.venv/current"

if [ ! -L "$CURRENT" ]; then
  echo "Dispatch shared runtime is not active at $CURRENT." >&2
  echo "Ask the Release Operator to run $ROOT_DIR/install.sh before onboarding." >&2
  exit 1
fi
RUNTIME=$(readlink -f "$CURRENT" 2>/dev/null || true)
if [ -z "$RUNTIME" ] || [ ! -f "$RUNTIME/.complete.json" ] || [ ! -x "$RUNTIME/bin/python" ]; then
  echo "Dispatch shared runtime is invalid at $CURRENT." >&2
  echo "Ask the Release Operator to reactivate a completed runtime." >&2
  exit 1
fi
if [ ! -x "$ROOT_DIR/bin/dispatch" ]; then
  echo "Shared Dispatch launcher is missing: $ROOT_DIR/bin/dispatch" >&2
  exit 1
fi
if [ ! -d "$DATA_ROOT" ] || [ ! -w "$DATA_ROOT" ]; then
  echo "$DATA_ROOT must exist and be writable" >&2
  exit 1
fi

mkdir -p "$DISPATCH_HOME/jobs" "$DISPATCH_HOME/telemetry"
chmod 700 "$DISPATCH_HOME" "$DISPATCH_HOME/jobs" "$DISPATCH_HOME/telemetry"
touch "$DISPATCH_HOME/dispatch.log"
chmod 600 "$DISPATCH_HOME/dispatch.log"

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
  "$RUNTIME/bin/python" - "$CONFIG_TMP" "$EMAIL" <<'PY'
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
chmod 600 "$CONFIG"

LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"
LAUNCHER_TMP="$LOCAL_BIN/.dispatch.tmp.$$"
trap 'rm -f "$LAUNCHER_TMP"' 0
cat > "$LAUNCHER_TMP" <<EOF
#!/usr/bin/env sh
exec "$ROOT_DIR/bin/dispatch" "\$@"
EOF
chmod 755 "$LAUNCHER_TMP"
mv "$LAUNCHER_TMP" "$LOCAL_BIN/dispatch"
trap - 0

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

echo
echo "Dispatch onboarding complete."
case ":$PATH:" in
  *":$LOCAL_BIN:"*) echo "The dispatch command is available in this shell." ;;
  *)
    echo "To use dispatch in this shell now:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "New shells will pick this up automatically from $SHELL_RC."
    ;;
esac
echo "Then cd to your SQL files and run: dispatch"

