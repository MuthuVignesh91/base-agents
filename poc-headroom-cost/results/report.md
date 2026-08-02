# Headroom cost/quality PoC — report

## Cost & tokens (mean per run)

| arm | runs | mean $ | median $ | in/out tok | cacheR/cacheW tok |
|---|---|---|---|---|---|
| baseline | 3 | $1.3669 | $1.2169 | 9/1947 | 496837/167961 |
| headroom | 3 | $0.3641 | $0.3647 | 3229/1457 | 66137/41494 |

**Cost reduction (mean): 73.4%**  (baseline $1.3669 -> headroom $0.3641)

## Answer quality (substring match vs known answers)

- **baseline**: 15/15 correct (100%)
- **headroom**: 15/15 correct (100%)

**Quality HELD** (baseline 100% vs headroom 100%)

## Headroom /stats (what it actually compressed)

```json
{
  "summary": {
    "mode": "token",
    "api_requests": 15,
    "primary_model": "claude-4.7-opus",
    "compression": {
      "requests_compressed": 6,
      "avg_compression_pct": 10.7,
      "best_compression_pct": 32.2,
      "best_detail": "26,939 \u2192 18,261 tokens",
      "total_tokens_removed": 17556,
      "cli_filtering_tokens_avoided": 0,
      "total_tokens_saved_with_cli_filtering": 17556,
      "total_tokens_before_with_cli_filtering": 183221,
      "rtk_tokens_avoided": 0,
      "total_tokens_saved_with_rtk": 17556,
      "total_tokens_before_with_rtk": 183221
    },
    "uncompressed_requests": {
      "prefix_frozen": 6,
      "too_small": 3,
      "passthrough": 3
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
    }
  },
  "agent_usage": {
    "agents": [
      {
        "agent": "claude-code",
        "label": "Claude",
        "source": "client",
        "requests": 18,
        "before_tokens": 183221,
        "after_tokens": 165665,
        "output_tokens": 6408,
        "tokens_saved": 17556,
        "models": {
          "claude-4.7-opus": 12,
          "claude-4.5-haiku": 3,
          "passthrough:count_tokens": 3
        },
        "providers": {
          "anthropic": 18
        },
        "has_exact_tokens": true,
        "savings_percent": 9.58,
        "after_percent": 90.42,
        "share_of_saved_percent": 100.0,
        "share_of_requests_percent": 100.0
      }
    ],
    "totals": {
      "requests": 18,
      "before_tokens": 183221,
      "after_tokens": 165665,
      "output_tokens": 6408,
      "tokens_saved": 17556,
      "savings_percent": 9.58
    },
    "coverage": {
      "logged_requests": 18,
      "exact_token_rows": 1,
      "mode": "request_logs"
    }
  },
  "savings": {
    "total_tokens": 17556,
    "per_project": {},
    "by_lay
```

## Per-run detail

### baseline
- run_1.json: $2.1882  in/out 10/2408  cacheR/W 498578/298124
- run_2.json: $1.2169  in/out 9/1562  cacheR/W 434823/150944
- run_3.json: $0.6955  in/out 9/1871  cacheR/W 557110/54815

### headroom
- run_1.json: $0.3745  in/out 3254/1610  cacheR/W 57809/43116
- run_2.json: $0.3532  in/out 3174/1607  cacheR/W 61665/38941
- run_3.json: $0.3647  in/out 3260/1154  cacheR/W 78937/42425
