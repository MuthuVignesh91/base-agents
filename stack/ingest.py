#!/usr/bin/env python3
"""Ingest a file (PDF, md, txt, docx, …) into a RAGFlow knowledge base.

Usage:
  python3 ingest.py <path-to-file> [kb_name]      # kb_name defaults to "book"

Creates the KB if needed, uploads the file, triggers parse (chunk + TEI embed),
and polls until parsing completes. Reads the RAGFlow API key from ./ragflow.env.
Large PDFs can take several minutes (DeepDoc parsing runs emulated on ARM).
"""
import json, os, sys, time, urllib.error, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = next(l.split("=", 1)[1].strip() for l in open(os.path.join(HERE, "ragflow.env"))
           if l.startswith("RAGFLOW_API_KEY="))
BASE = "http://localhost:9380/api/v1"


def req(method, path, data=None, raw=None, ctype="application/json"):
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    r = urllib.request.Request(BASE + path, data=body, method=method,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": ctype})
    try:
        resp = urllib.request.urlopen(r, timeout=180); return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    if len(sys.argv) < 2:
        print("usage: python3 ingest.py <file> [kb_name]"); sys.exit(1)
    path, kb = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "book")
    if not os.path.isfile(path):
        print("file not found:", path); sys.exit(1)

    # find or create KB
    ds = (req("GET", "/datasets?page=1&page_size=100")[1].get("data")) or []
    did = next((d["id"] for d in ds if d.get("name") == kb), None)
    if did:
        print(f"using existing KB '{kb}' -> {did}")
    else:
        _, d = req("POST", "/datasets", {"name": kb})
        did = (d.get("data") or {}).get("id")
        print(f"created KB '{kb}' -> {did} (embedder={(d.get('data') or {}).get('embedding_model')})")
    if not did:
        print("could not resolve KB"); sys.exit(1)

    # upload (multipart)
    content = open(path, "rb").read()
    fn = os.path.basename(path)
    b = "----hb" + uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{fn}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n").encode() + content + f"\r\n--{b}--\r\n".encode()
    _, d = req("POST", f"/datasets/{did}/documents", raw=body, ctype="multipart/form-data; boundary=" + b)
    docs = d.get("data") or []
    doc_id = docs[0]["id"] if docs else None
    print(f"uploaded {fn} ({len(content)//1024} KB) -> doc {doc_id} | code={d.get('code')} {d.get('message') or ''}")
    if not doc_id:
        sys.exit(1)

    # trigger parse
    _, d = req("POST", f"/datasets/{did}/chunks", {"document_ids": [doc_id]})
    print(f"parse triggered | code={d.get('code')} {d.get('message') or ''}")
    print("parsing (large PDFs can take several minutes)...")
    while True:
        _, d = req("GET", f"/datasets/{did}/documents?page=1&page_size=50")
        rows = (d.get("data") or {}).get("docs") or d.get("data") or []
        doc = next((x for x in rows if x.get("id") == doc_id), {})
        run, prog = doc.get("run"), doc.get("progress")
        ck = doc.get("chunk_count") or doc.get("chunk_num")
        print(f"  run={run} progress={prog} chunks={ck}")
        if run == "DONE" or (isinstance(prog, (int, float)) and prog >= 1):
            print(f"DONE — {ck} chunks. Ask with:  KB={kb} python3 query.py \"...\"  or the agent.")
            break
        if run == "FAIL":
            print("PARSE FAILED — check the RAGFlow UI (Knowledge Base -> the doc -> logs)."); break
        time.sleep(10)


if __name__ == "__main__":
    main()
