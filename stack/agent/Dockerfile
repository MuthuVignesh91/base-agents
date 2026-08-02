# RAG agent = claude-cli (headless) that retrieves via RAGFlow MCP and
# reasons via headroom -> llm-gateway. Run on demand (not part of `up`).
FROM node:22-slim

# npmjs.org is blocked on the corp network — use an internal Artifactory npm
# mirror. Pinned to a version present on the mirror.
RUN npm config set registry https://artifactory.example.internal/artifactory/api/npm/npm-registry \
 && npm install -g @anthropic-ai/claude-code@2.1.128

WORKDIR /work
COPY .mcp.json system-prompt.txt run.sh /work/
RUN chmod +x /work/run.sh && chown -R node:node /work

# claude-cli refuses bypassPermissions as root — run as the image's non-root 'node' user.
USER node

# Container stays alive as a long-lived service. Query it with:
#   docker exec agent /work/run.sh -p "your question"
# (run.sh wires the fixed flags: MCP config, system prompt, model.)
CMD ["sleep", "infinity"]
