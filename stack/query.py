#!/usr/bin/env python3
"""Query the RAGFlow knowledge base from the terminal (retrieval only).

Usage:
  python3 query.py "What port does payments-service listen on?"

Returns the top matching chunks + similarity scores from the 'poc-payments' KB.
This is pure retrieval (what the agent's `retrieve` tool sees) — not a generated
answer. Reads the RAGFlow API key from ./ragflow.env.
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = next(l.split("=", 1)[1].strip() for l in open(os.path.join(HERE, "ragflow.env"))
           if l.startswith("RAGFLOW_API_KEY="))
BASE = "http://localhost:9380/api/v1"


def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())


def main():
    q = " ".join(sys.argv[1:]).strip() or "What port does payments-service listen on?"
    kb = os.environ.get("KB", "poc-payments")   # override: KB=mybook python3 query.py "..."
    ds = req("GET", "/datasets?page=1&page_size=50").get("data") or []
    did = next((d["id"] for d in ds if d.get("name") == kb), ds[0]["id"] if ds else None)
    if not did:
        print("No knowledge base found."); sys.exit(1)
    d = req("POST", "/retrieval", {"question": q, "dataset_ids": [did],
                                   "top_k": 5, "similarity_threshold": 0.0})
    chunks = (d.get("data") or {}).get("chunks") or []
    print(f"Q: {q}\n{len(chunks)} chunk(s) retrieved:\n")
    for i, c in enumerate(chunks, 1):
        score = c.get("similarity", c.get("score"))
        txt = (c.get("content_with_weight") or c.get("content") or "").strip()
        print(f"[{i}] score={score}\n{txt}\n")


if __name__ == "__main__":
    main()
