#!/usr/bin/env python3
"""Generate the RAG-scale synthetic dataset for the Headroom PoC.

Deterministic (seed=42): regenerating produces identical files. Overwrites
app.log and metrics.json in this directory. config.json and service.py are
hand-authored and left untouched.

The dataset is sized so that reading it produces *bulk* tool outputs (tens of
thousands of tokens) — the compressible surface Headroom is meant to crush —
while staying well under the 200k context window (base context is ~111k).

Controlled facts (so questions have unambiguous answers):
  - highest p99 latency        -> endpoint "payouts"  (single row = 1180ms)
  - highest error rate         -> endpoint "webhooks" (single row = 0.052)
  - gateway-timeout transaction-> "txn_10482" (one ERROR line in app.log)
  - listen port / db host / default currency come from config.json / service.py
"""
import json
import os
import random
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(42)

ENDPOINTS = [
    "charges", "checkout", "refunds", "payouts", "webhooks", "customers",
    "balance", "invoices", "subscriptions", "tokens", "disputes", "health",
    "transfers", "mandates", "sources",
]
METHODS = {
    "charges": "POST", "checkout": "GET", "refunds": "POST", "payouts": "POST",
    "webhooks": "POST", "customers": "GET", "balance": "GET", "invoices": "GET",
    "subscriptions": "GET", "tokens": "POST", "disputes": "GET", "health": "GET",
    "transfers": "POST", "mandates": "POST", "sources": "POST",
}
REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]

# ---- metrics.json : per-endpoint, per-hour time series (15 x 24 = 360 rows) ----
rows = []
for ep in ENDPOINTS:
    for hour in range(24):
        p50 = random.randint(5, 200)
        p95 = p50 + random.randint(40, 400)
        p99 = min(1170, p95 + random.randint(20, 300))          # cap < 1180
        err = round(random.uniform(0.0, 0.045), 4)              # cap < 0.052
        rows.append({
            "endpoint": ep, "method": METHODS[ep], "hour": f"{hour:02d}:00",
            "requests": random.randint(50, 4000), "error_rate": err,
            "p50_ms": p50, "p95_ms": p95, "p99_ms": p99,
        })

# Inject the controlled global maxima.
for r in rows:
    if r["endpoint"] == "payouts" and r["hour"] == "14:00":
        r["p99_ms"] = 1180                                      # unique highest p99
    if r["endpoint"] == "webhooks" and r["hour"] == "03:00":
        r["error_rate"] = 0.052                                 # unique highest error rate
    if r["endpoint"] == "checkout" and r["hour"] == "12:00":
        r["p99_ms"] = 842                                       # recognizable datapoint

metrics = {"generated_at": "2026-07-18T23:59:00Z", "window": "24h", "interval": "1h", "endpoints": rows}
with open(os.path.join(HERE, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)
    f.write("\n")

# ---- app.log : ~1500 request lines + startup/shutdown + one injected ERROR ----
start = datetime(2026, 7, 18, 9, 0, 0)
lines = [
    f"{start.isoformat()}Z INFO  [startup] payments-service 3.4.1 listening on 0.0.0.0:8443",
    f"{start.isoformat()}Z INFO  [startup] connected to database pg-primary.internal:5432 (pool=20)",
]
t = start
for _ in range(1500):
    t = t + timedelta(seconds=random.randint(1, 25))
    ts = t.isoformat() + "Z"
    ep = random.choice(ENDPOINTS)
    method = METHODS[ep]
    region = random.choice(REGIONS)
    roll = random.random()
    if roll < 0.03:
        lines.append(f"{ts} INFO  [http] {method} /v2/{ep} status=500 dur={random.randint(5000, 30000)}ms region={region}")
    elif roll < 0.08:
        lines.append(f"{ts} WARN  [gateway] slow response from upstream: {random.randint(1500, 2500)}ms (retry 1/3)")
    else:
        lines.append(f"{ts} INFO  [http] {method} /v2/{ep} status=200 dur={random.randint(20, 900)}ms region={region}")

# Inject the one gateway-timeout transaction (the only "gateway timeout" in the file).
inject_at = len(lines) // 2
err_ts = (start + timedelta(hours=5, minutes=24, seconds=55)).isoformat() + "Z"
lines.insert(inject_at, f"{err_ts} INFO  [http] POST /v2/charges status=500 dur=30001ms region=eu-west-1")
lines.insert(inject_at + 1, f"{err_ts} ERROR [gateway] transaction txn_10482 failed: gateway timeout after 30000ms")
lines.append(f"{(t + timedelta(minutes=5)).isoformat()}Z INFO  [shutdown] draining connections, graceful_shutdown=20s")

with open(os.path.join(HERE, "app.log"), "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"metrics.json: {len(rows)} rows")
print(f"app.log: {len(lines)} lines")
