# Headroom compression+router proxy (single container).
# Pinned to the version validated in the cost PoC.
FROM python:3.13-slim

RUN pip install --no-cache-dir "headroom-ai[proxy]==0.32.1" \
    && mkdir -p /logs

EXPOSE 8787

# ENTRYPOINT is the binary; docker-compose supplies the `proxy ...` args
# (with --mode / --backend interpolated from .env) as the command.
ENTRYPOINT ["headroom"]
CMD ["proxy", "--host", "0.0.0.0", "--port", "8787", "--log-file", "/logs/proxy.jsonl"]
