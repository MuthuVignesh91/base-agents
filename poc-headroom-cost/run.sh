#!/usr/bin/env bash
#
# run.sh — run the Headroom cost/quality A/B.
#
#   ./run.sh [N] [arm]
#     N    number of runs per arm (default: 5)
#     arm  baseline | headroom | both (default: both)
#
# Each run invokes claude-cli headless on the fixed investigation task and saves
# the raw --output-format json to results/<arm>/run_<i>.json.
#
# Baseline arm : claude-cli straight to Anthropic.
# Headroom arm : same task, but ANTHROPIC_BASE_URL points at a local Headroom
#                proxy (compression) which forwards upstream. /stats is snapshot
#                after the runs.
#
# NOTE on env scrubbing: this script strips inherited ANTHROPIC_*/routing env
# vars before invoking claude. If you run it from inside another Claude Code
# session (or any shell that exports ANTHROPIC_AUTH_TOKEN / ANTHROPIC_BASE_URL),
# the nested claude would inherit them and fail auth (401). Scrubbing forces
# claude to use its own stored credentials — i.e. a normal user invocation.
#
# Env overrides: MODEL (default opus), HEADROOM_PORT (default 8787).
set -euo pipefail

N="${1:-5}"
ARM="${2:-both}"
MODEL="${MODEL:-opus}"
PORT="${HEADROOM_PORT:-8787}"
# Headroom's upstream. Defaults to the LLM gateway from ~/.claude/settings.json
# so the proxy forwards claude's gateway token to the right place (fixes 401).
UPSTREAM="${HEADROOM_UPSTREAM:-https://llm-gateway.example.internal}"
HR_MODE="${HEADROOM_MODE:-cache}"   # cache = freeze prefix (protect cache) | token = compress (may bust cache)
ALLOWED_TOOLS="Read,Grep,Glob,Bash"

POC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$POC_DIR/.." && pwd)"
HEADROOM_BIN="$BASE_DIR/.venv/bin/headroom"
PROMPT_FILE="$POC_DIR/task/prompt.txt"
RESULTS="$POC_DIR/results"

# Strip inherited routing/auth env so claude uses its own stored credentials.
SCRUB=(env
  -u ANTHROPIC_BASE_URL
  -u ANTHROPIC_API_KEY
  -u ANTHROPIC_AUTH_TOKEN
  -u ANTHROPIC_CUSTOM_HEADERS
  -u ANTHROPIC_MODEL
  -u ANTHROPIC_SMALL_FAST_MODEL
  -u ANTHROPIC_DEFAULT_HAIKU_MODEL
  -u CLAUDE_CODE_USE_BEDROCK
  -u CLAUDE_CODE_USE_VERTEX
)

cd "$POC_DIR"   # so claude-cli's file tools see ./dataset
mkdir -p "$RESULTS/baseline" "$RESULTS/headroom"
PROMPT="$(cat "$PROMPT_FILE")"

cost_of () { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('total_cost_usd','?'))" "$1" 2>/dev/null || echo '?'; }

run_one () {  # $1=arm  $2=index  $3=base_url (optional -> headroom arm)
  local arm="$1" i="$2" baseurl="${3:-}" out
  out="$RESULTS/$arm/run_$i.json"
  if [ -n "$baseurl" ]; then
    "${SCRUB[@]}" ANTHROPIC_BASE_URL="$baseurl" \
      claude -p "$PROMPT" --model "$MODEL" --allowedTools "$ALLOWED_TOOLS" --output-format json </dev/null >"$out"
  else
    "${SCRUB[@]}" \
      claude -p "$PROMPT" --model "$MODEL" --allowedTools "$ALLOWED_TOOLS" --output-format json </dev/null >"$out"
  fi
  echo "  [$arm] run $i/$N  ->  \$$(cost_of "$out")"
}

run_baseline () {
  echo "== BASELINE arm ($N runs, model=$MODEL) — direct to Anthropic =="
  for i in $(seq 1 "$N"); do run_one baseline "$i"; done
}

run_headroom () {
  echo "== HEADROOM arm ($N runs, model=$MODEL, mode=$HR_MODE) — via proxy on :$PORT -> $UPSTREAM =="
  [ -x "$HEADROOM_BIN" ] || { echo "ERROR: headroom not found at $HEADROOM_BIN"; exit 1; }

  ANTHROPIC_TARGET_API_URL="$UPSTREAM" "$HEADROOM_BIN" proxy --port "$PORT" --mode "$HR_MODE" --log-file "$RESULTS/headroom/proxy.jsonl" >"$RESULTS/headroom/proxy.stdout.log" 2>&1 &
  local proxy_pid=$!
  trap 'kill "$proxy_pid" 2>/dev/null || true' EXIT

  local ready=""
  for _ in $(seq 1 30); do
    if curl -sf "http://localhost:$PORT/stats" >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
  done
  [ -n "$ready" ] || { echo "ERROR: Headroom proxy not ready on :$PORT — aborting (refusing to measure un-proxied calls). See $RESULTS/headroom/proxy.stdout.log"; exit 1; }
  echo "  proxy ready on :$PORT"

  for i in $(seq 1 "$N"); do run_one headroom "$i" "http://localhost:$PORT"; done

  curl -s "http://localhost:$PORT/stats" >"$RESULTS/headroom/stats.json" 2>/dev/null || true
  echo "  saved proxy /stats -> $RESULTS/headroom/stats.json"
  kill "$proxy_pid" 2>/dev/null || true
  trap - EXIT
}

case "$ARM" in
  baseline) run_baseline ;;
  headroom) run_headroom ;;
  both)     run_baseline; run_headroom ;;
  *) echo "unknown arm: $ARM (use baseline|headroom|both)"; exit 1 ;;
esac

echo "Done. Raw results in $RESULTS/. Next: python3 score.py && python3 compare.py"
