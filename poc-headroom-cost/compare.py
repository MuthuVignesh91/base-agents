#!/usr/bin/env python3
"""Aggregate the Headroom PoC results into results/report.md.

Reads the raw run JSON (cost + token usage) from both arms, the quality scores
from results/scores.json (run score.py first), and Headroom's /stats snapshot if
present. Emits a markdown report and prints it. No API calls.
"""
import glob
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")


def load_runs(arm):
    runs = []
    for p in sorted(glob.glob(os.path.join(RESULTS, arm, "run_*.json"))):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        u = d.get("usage", {}) or {}
        runs.append({
            "file": os.path.basename(p),
            "cost": d.get("total_cost_usd", 0) or 0,
            "in": u.get("input_tokens", 0) or 0,
            "out": u.get("output_tokens", 0) or 0,
            "cache_read": u.get("cache_read_input_tokens", 0) or 0,
            "cache_create": u.get("cache_creation_input_tokens", 0) or 0,
            "is_error": bool(d.get("is_error")),
        })
    return runs


def mean(runs, key):
    vals = [r[key] for r in runs]
    return st.mean(vals) if vals else 0


def load_scores():
    p = os.path.join(RESULTS, "scores.json")
    if not os.path.exists(p):
        return {}
    s = json.load(open(p))
    out = {}
    for arm, rs in s.items():
        scored = [r for r in rs if "passed" in r]
        out[arm] = {
            "passed": sum(r["passed"] for r in scored),
            "total": sum(r["total"] for r in scored),
        }
    return out


def main():
    base = load_runs("baseline")
    head = load_runs("headroom")
    scores = load_scores()
    L = ["# Headroom cost/quality PoC — report", ""]

    # --- cost & tokens ---
    L += ["## Cost & tokens (mean per run)", "",
          "| arm | runs | mean $ | median $ | in/out tok | cacheR/cacheW tok |",
          "|---|---|---|---|---|---|"]
    for name, runs in (("baseline", base), ("headroom", head)):
        if not runs:
            L.append(f"| {name} | 0 | - | - | - | - |")
            continue
        costs = [r["cost"] for r in runs]
        L.append(f"| {name} | {len(runs)} | ${st.mean(costs):.4f} | ${st.median(costs):.4f} | "
                 f"{mean(runs,'in'):.0f}/{mean(runs,'out'):.0f} | "
                 f"{mean(runs,'cache_read'):.0f}/{mean(runs,'cache_create'):.0f} |")
    L.append("")
    if base and head:
        bm, hm = mean(base, "cost"), mean(head, "cost")
        red = (bm - hm) / bm * 100 if bm else 0
        L += [f"**Cost reduction (mean): {red:.1f}%**  (baseline ${bm:.4f} -> headroom ${hm:.4f})", ""]

    # --- quality ---
    L += ["## Answer quality (substring match vs known answers)", ""]
    if scores:
        for arm in ("baseline", "headroom"):
            s = scores.get(arm)
            if s and s["total"]:
                L.append(f"- **{arm}**: {s['passed']}/{s['total']} correct ({s['passed']/s['total']*100:.0f}%)")
        b, h = scores.get("baseline"), scores.get("headroom")
        if b and h and b["total"] and h["total"]:
            bq, hq = b["passed"] / b["total"], h["passed"] / h["total"]
            L += ["", f"**Quality {'HELD' if hq >= bq else 'DROPPED'}** "
                      f"(baseline {bq*100:.0f}% vs headroom {hq*100:.0f}%)"]
    else:
        L.append("_No scores.json — run `python3 score.py` first._")
    L.append("")

    # --- headroom /stats ---
    sp = os.path.join(RESULTS, "headroom", "stats.json")
    if os.path.exists(sp):
        try:
            hstats = json.load(open(sp))
            L += ["## Headroom /stats (what it actually compressed)", "",
                  "```json", json.dumps(hstats, indent=2)[:2500], "```", ""]
        except Exception:
            pass

    # --- per-run detail ---
    L += ["## Per-run detail", ""]
    for arm, runs in (("baseline", base), ("headroom", head)):
        L.append(f"### {arm}")
        for r in runs:
            err = "  [API ERROR]" if r["is_error"] else ""
            L.append(f"- {r['file']}: ${r['cost']:.4f}  in/out {r['in']}/{r['out']}  "
                     f"cacheR/W {r['cache_read']}/{r['cache_create']}{err}")
        L.append("")

    report = "\n".join(L)
    os.makedirs(RESULTS, exist_ok=True)
    open(os.path.join(RESULTS, "report.md"), "w").write(report)
    print(report)


if __name__ == "__main__":
    main()
