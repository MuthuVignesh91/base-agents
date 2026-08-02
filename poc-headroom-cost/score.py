#!/usr/bin/env python3
"""Score answer quality for the Headroom PoC.

Substring-matches each run's final answer text against the known-good answers in
task/questions.json (case-insensitive). Writes results/scores.json and prints a
per-run summary. Deterministic; no API calls.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
QUESTIONS = json.load(open(os.path.join(HERE, "task", "questions.json")))


def score_run(path):
    try:
        d = json.load(open(path))
    except Exception:
        return {"file": os.path.basename(path), "error": "unparseable"}
    text = (d.get("result") or "").lower()
    failures = [q["id"] for q in QUESTIONS if q["expected"].lower() not in text]
    return {
        "file": os.path.basename(path),
        "passed": len(QUESTIONS) - len(failures),
        "total": len(QUESTIONS),
        "failures": failures,
        "is_error": bool(d.get("is_error")),
    }


def main():
    out = {}
    for arm in ("baseline", "headroom"):
        runs = sorted(glob.glob(os.path.join(RESULTS, arm, "run_*.json")))
        out[arm] = [score_run(p) for p in runs]

    os.makedirs(RESULTS, exist_ok=True)
    json.dump(out, open(os.path.join(RESULTS, "scores.json"), "w"), indent=2)

    for arm, rs in out.items():
        print(f"[{arm}] {len(rs)} run(s)")
        for r in rs:
            if "error" in r:
                print(f"  {r['file']}: UNPARSEABLE")
                continue
            detail = "all pass" if not r["failures"] else "fails Q" + ",".join(map(str, r["failures"]))
            err = " [API ERROR]" if r["is_error"] else ""
            print(f"  {r['file']}: {r['passed']}/{r['total']} ({detail}){err}")


if __name__ == "__main__":
    main()
