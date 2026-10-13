FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples

RUN python -m pip install --no-cache-dir . \
    && useradd --system --uid 10001 --home-dir /nonexistent mcp-trace

ENV MCP_TRACE_DIR=/app/examples
USER mcp-trace
CMD ["mcp-trace-inspector"]
