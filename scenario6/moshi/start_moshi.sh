#!/usr/bin/env bash
set -euo pipefail

SSL_DIR=${MOSHI_SSL_DIR:-/ssl}
CPU_OFFLOAD=${MOSHI_CPU_OFFLOAD:-0}

ARGS=("-m" "moshi.server" "--ssl" "$SSL_DIR")
if [[ "$CPU_OFFLOAD" == "1" || "$CPU_OFFLOAD" == "true" || "$CPU_OFFLOAD" == "yes" ]]; then
  ARGS+=("--cpu-offload")
fi

exec python "${ARGS[@]}"
