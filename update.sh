#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REMOTE_NAME=${DISPATCH_UPDATE_REMOTE:-${GIT_REMOTE:-bitbucket}}
BRANCH_NAME=${DISPATCH_UPDATE_BRANCH:-${GIT_BRANCH:-main}}
REMOTE_REF="refs/remotes/$REMOTE_NAME/$BRANCH_NAME"
TARGET_REF=${1:-$REMOTE_REF}

cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "$ROOT_DIR is not a Git working tree" >&2
  exit 1
fi

git fetch --prune "$REMOTE_NAME" "$BRANCH_NAME:$REMOTE_REF"
git reset --hard "$TARGET_REF"

# Keep the shared tree readable/traversable for analysts. Git restores tracked
# executable bits during reset; a+rX preserves those bits while fixing directory
# traversal and read permissions. Untracked runtime/vendor files are preserved.
chmod 755 "$ROOT_DIR"
chmod -R a+rX "$ROOT_DIR"

echo "Dispatch shared tree updated:"
echo "  path:   $ROOT_DIR"
echo "  remote: $REMOTE_NAME"
echo "  branch: $BRANCH_NAME"
echo "  commit: $(git rev-parse --short HEAD)"
