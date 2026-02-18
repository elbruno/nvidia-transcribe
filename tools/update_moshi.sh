#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${1:-"https://github.com/NVIDIA/personaplex.git"}
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEST_ROOT="$ROOT_DIR/scenario6/third_party"
DEST="$DEST_ROOT/moshi"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$DEST_ROOT"

if [[ -d "$DEST" ]]; then
  BACKUP="$DEST_ROOT/moshi_prev_$TIMESTAMP"
  mv "$DEST" "$BACKUP"
  echo "Backed up existing moshi to $BACKUP"
fi

TMP_DIR=$(mktemp -d)
REPO_DIR="$TMP_DIR/personaplex"

git clone --depth 1 "$REPO_URL" "$REPO_DIR"
cp -R "$REPO_DIR/moshi" "$DEST"

LICENSE_FILE=$(ls "$REPO_DIR"/LICENSE* 2>/dev/null | head -n 1 || true)
if [[ -n "$LICENSE_FILE" ]]; then
  cp "$LICENSE_FILE" "$DEST/"
fi

git -C "$REPO_DIR" rev-parse HEAD > "$DEST/MOSHI_VERSION"

rm -rf "$TMP_DIR"

echo "Moshi vendored at $DEST"
cat "$DEST/MOSHI_VERSION"
