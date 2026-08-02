# base-agents — RAG agent stack (PoC)

A single Docker stack (`base-agents` compose project) that runs a
retrieval-augmented **agent**: `claude-cli` retrieves from a RAGFlow knowledge
base via MCP and reasons through **Headroom** (context-compression proxy) →
**llm-gateway** (an internal LiteLLM gateway).

```
agent (claude-cli) ─MCP :9382─▶ ragflow-cpu ─▶ tei + infinity + mysql + minio + redis   (RETRIEVE)
                   └reason :8787▶ headroom ────▶ llm-gateway                             (ANSWER, compressed)
```

## Containers

| Service | Role |
|---|---|
| `agent` | `claude-cli` + RAG system prompt. **Always-on** service; query via `docker exec`. Retrieves via MCP, reasons via headroom. |
| `headroom` | Compression + provider router. Forwards to llm-gateway (flip provider in `.env`). |
| `ragflow-cpu` | RAG engine + **MCP retrieve server** (:9382, self-host/SSE). |
| `tei-cpu` | Local embeddings — `bge-small-en-v1.5` (used at ingest + query). |
| `infinity` | Vector + full-text index; runs the hybrid search. |
| `mysql` | Catalog/metadata (KBs, docs, chunk records, API keys, account). |
| `minio` | Object storage for raw uploaded files. |
| `redis` (valkey) | Parse/ingest task queue + cache. |

## Prerequisites

- Docker Desktop with ~**10–12 GB** allocated to the VM (Settings → Resources).
- Two gitignored env files under `stack/`:
  - **`.env`** — Headroom + project config. Must contain:
    ```
    HEADROOM_MODE=token
    HEADROOM_PORT=8787
    HEADROOM_BACKEND=anthropic
    ANTHROPIC_TARGET_API_URL=https://llm-gateway.example.internal
    COMPOSE_PROFILES=infinity,cpu,tei-cpu     # activates RAGFlow services
    MCP_HOST_API_KEY=ragflow-xxxx             # RAGFlow API key (for MCP self-host)
    AIHUB_TOKEN=sk-xxxx                        # llm-gateway token (agent auth via headroom)
    ```
  - **`ragflow.env`** — `RAGFLOW_API_KEY=ragflow-xxxx` (used by `query.py`).
- `ragflow/` is RAGFlow's official deploy, vendored at tag **v0.26.4** (gitignored).
  Its knobs live in `ragflow/docker/.env` (`DOC_ENGINE=infinity`, TEI `bge-small`,
  `SVR_WEB_HTTP_PORT=8080`, `MACOS=1`).

## Bring the stack up

```bash
cd stack
docker compose up -d          # starts all 8 containers, including the always-on agent
docker compose ps             # wait for healthy; RAGFlow UI = http://localhost:8080
```

## Store knowledge (ingest)

Via the RAGFlow UI: **http://localhost:8080** → Knowledge Base **poc-payments** →
upload a file → it parses (chunk → TEI embed → infinity). Immediately retrievable.

## Query — three ways

**1. The agent (generated answer, cites sources)** — always-on container, query via exec:
```bash
docker exec agent /work/run.sh -p "What port does payments-service listen on?"
```

**2. Retrieval only (raw chunks), terminal:**
```bash
python3 stack/query.py "which endpoint has the highest error rate?"
```

**3. Retrieval only, UI:** localhost:8080 → KB → *Retrieval testing*.

## Flip the LLM provider (Headroom)

Edit `stack/.env` → `docker compose up -d headroom`:
- **llm-gateway (default):** `HEADROOM_BACKEND=anthropic` + `ANTHROPIC_TARGET_API_URL=…llm-gateway…`
- **OpenRouter:** `HEADROOM_BACKEND=openrouter` + `OPENROUTER_API_KEY=…`
- **local Ollama:** `HEADROOM_BACKEND=anyllm` + `HEADROOM_ANYLLM_PROVIDER=ollama` + `OPENAI_TARGET_API_URL=http://host.docker.internal:11434/v1`

`HEADROOM_MODE`: `token` (compress, best for RAG) or `cache` (protect prefix cache).

## Gotchas (learned building this)

- **npmjs.org is blocked** on the corp network → the `agent` image installs
  claude-cli from an internal Artifactory npm mirror (`agent/Dockerfile`).
- The agent runs as the **non-root `node` user** (claude-cli refuses
  `bypassPermissions` as root).
- RAGFlow deploy files **must match the image tag** (v0.26.4) — the compose
  mounts `entrypoint.sh`, so a newer clone + older image crash-loops.
- RAGFlow's MCP must be enabled with `--enable-mcpserver --mcp-host=0.0.0.0`
  (default binds 127.0.0.1, unreachable from the agent). Self-host mode → SSE
  only (`--no-transport-streamable-http-enabled`). Set in the top-level compose's
  `ragflow-cpu` override.
- **Never `docker compose down -v`** unless you want a full reset — `-v` wipes
  the mysql/infinity/minio volumes (account, API key, and all ingested docs).
- RAGFlow image is `amd64` → runs emulated on Apple Silicon (works, slower).
