#!/usr/bin/env bash
# Entrypoint for the RAG agent container. Fixed flags here; the caller's args
# (e.g. -p "question") are appended via "$@".
set -euo pipefail
exec claude \
  --mcp-config /work/.mcp.json \
  --permission-mode bypassPermissions \
  --append-system-prompt "$(cat /work/system-prompt.txt)" \
  --model "${ANTHROPIC_MODEL:-claude-sonnet-4-6}" \
  "$@"
