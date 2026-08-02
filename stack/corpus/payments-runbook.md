# payments-service Runbook

## Overview
`payments-service` is the core charge and refund service. It listens on **TCP port 8443**.

## Configuration
- Listen port: **8443**
- Database primary host: **pg-primary.internal** (read replica: pg-replica.internal)
- Payment gateway: stripe — max **3** retries, **30s** timeout
- Allowed regions: us-east-1, us-west-2, eu-west-1
- Maximum charge amount: 500000 cents

## Code notes
The `charge()` function defaults to currency **USD** when the caller does not specify one.
Supported currencies: USD, EUR, GBP.

## Known incidents
On 2026-07-18, transaction **txn_10482** failed with a **"gateway timeout"** after
30000ms while charging against the eu-west-1 region.

## Endpoint metrics (last 24h)
Across all endpoints, **payouts** has the **highest p99 latency (1180 ms)**, and
**webhooks** has the **highest error rate (0.052)**. For reference, the checkout
endpoint p99 latency is 842 ms.
