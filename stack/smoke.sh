#!/usr/bin/env bash
#
# smoke.sh — confirm the containerized chain works:
#   claude-cli (host) -> Headroom (container :PORT) -> provider (per .env)
#
# Assumes `docker compose up -d` is running. For the default llm-gateway profile,
# claude-cli's token comes from ~/.claude/settings.json (we scrub inherited
# routing env so a nested/polluted shell still falls back to it).
set -euo pipefail

PORT="${HEADROOM_PORT:-8787}"

echo "1) Headroom container reachable on :$PORT ?"
curl -sf "http://localhost:$PORT/stats" >/dev/null \
  || { echo "   NO — is 'docker compose up -d' running? (docker compose ps)"; exit 1; }
echo "   yes."

echo "2) Round-trip claude-cli -> Headroom(:$PORT) -> provider ..."
env -u ANTHROPIC_BASE_URL -u ANTHROPIC_AUTH_TOKEN -u ANTHROPIC_API_KEY -u ANTHROPIC_MODEL -u ANTHROPIC_SMALL_FAST_MODEL \
  ANTHROPIC_BASE_URL="http://localhost:$PORT" \
  claude -p "Reply with exactly: STACK OK" --model "${SMOKE_MODEL:-opus}" --output-format json </dev/null \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print('   is_error:',d.get('is_error'),'| result:',repr(d.get('result'))[:60],'| cost:',d.get('total_cost_usd'))"

echo "3) Headroom saw the request:"
curl -s "http://localhost:$PORT/stats" \
  | python3 -c "import json,sys;s=json.load(sys.stdin)['summary'];print('   api_requests:',s['api_requests'],'| mode:',s['mode'],'| model:',s.get('primary_model'))"
echo "Stack OK."
