# Headroom cost/quality PoC — report

## Cost & tokens (mean per run)

| arm | runs | mean $ | median $ | in/out tok | cacheR/cacheW tok |
|---|---|---|---|---|---|
| baseline | 3 | $1.3669 | $1.2169 | 9/1947 | 496837/167961 |
| headroom | 3 | $0.3727 | $0.3225 | 3144/1353 | 69658/42534 |

**Cost reduction (mean): 72.7%**  (baseline $1.3669 -> headroom $0.3727)

## Answer quality (substring match vs known answers)

- **baseline**: 15/15 correct (100%)
- **headroom**: 15/15 correct (100%)

**Quality HELD** (baseline 100% vs headroom 100%)

## Headroom /stats (what it actually compressed)

```json
{
  "summary": {
    "mode": "cache",
    "api_requests": 15,
    "primary_model": "claude-4.7-opus",
    "compression": {
      "requests_compressed": 0,
      "avg_compression_pct": 0.0,
      "best_compression_pct": 0.0,
      "best_detail": "",
      "total_tokens_removed": 0,
      "cli_filtering_tokens_avoided": 0,
      "total_tokens_saved_with_cli_filtering": 0,
      "total_tokens_before_with_cli_filtering": 179317,
      "rtk_tokens_avoided": 0,
      "total_tokens_saved_with_rtk": 0,
      "total_tokens_before_with_rtk": 179317
    },
    "uncompressed_requests": {
      "prefix_frozen": 15,
      "passthrough": 4
    },
    "cost": {
      "without_headroom_usd": 0.0,
      "with_headroom_usd": 0.0,
      "total_saved_usd": 0.0,
      "savings_pct": 0.0,
      "breakdown": {
        "cache_savings_usd": 0.0,
        "compression_savings_usd": 0.0,
        "cli_filtering_savings_usd": null,
        "cli_filtering_savings_note": "CLI filtering tokens are included in token savings only; dollar savings use proxy compression tokens at model list price.",
        "rtk_savings_usd": null,
        "rtk_savings_note": "CLI filtering tokens are included in token savings only; dollar savings use proxy compression tokens at model list price."
      }
    },
    "mcp": {
      "compressions": 0,
      "tokens_removed": 0,
      "retrievals": 0
    },
    "tip": "Most requests are prefix-frozen. Set HEADROOM_MODE=token to compress frozen messages and extend your session by ~25-35%."
  },
  "agent_usage": {
    "agents": [
      {
        "agent": "claude-code",
        "label": "Claude",
        "source": "client",
        "requests": 19,
        "before_tokens": 179317,
        "after_tokens": 179317,
        "output_tokens": 6498,
        "tokens_saved": 0,
        "models": {
          "claude-4.7-opus": 12,
          "claude-4.5-haiku": 3,
          "passthrough:count_tokens": 4
        },
        "providers": {
          "anthropic": 19
        },
        "has_exact_tokens": true,
        "savings_percent": 0.0,
        "after_percent": 100.0,
        "share_of_saved_percent": 0.0,
        "share_of_requests_percent": 100.0
      }
    ],
    "totals": {
      "requests": 19,
      "before_tokens": 179317,
      "after_tokens": 179317,
      "output_tokens": 6498,
      "tokens_saved": 0,
      "savings_percent": 0.0
    },
    "coverage": {
      "logged_requests": 19,
      "exact_token_rows": 1,
      "mode": "request_logs"
    }
  },
  "savings": {

```

## Per-run detail

### baseline
- run_1.json: $2.1882  in/out 10/2408  cacheR/W 498578/298124
- run_2.json: $1.2169  in/out 9/1562  cacheR/W 434823/150944
- run_3.json: $0.6955  in/out 9/1871  cacheR/W 557110/54815

### headroom
- run_1.json: $0.4884  in/out 3174/1319  cacheR/W 69646/60576
- run_2.json: $0.3225  in/out 2999/1681  cacheR/W 69536/33684
- run_3.json: $0.3072  in/out 3258/1059  cacheR/W 69791/33343
