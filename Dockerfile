# Google Media MCP Server — Remote HTTP MCP server exposing Vertex AI
# (Imagen / Veo) as Claude Code tools. Built for Google Cloud Run.
#
# Build:  docker build -t google-media-mcp .
# Run:    docker run -p 8080:8080 --env-file .env google-media-mcp
#
# No credentials are baked into this image. On Cloud Run, auth to Vertex AI
# is via Application Default Credentials (the service's attached service
# account) — see docs/GOOGLE_MEDIA_MCP.md. Locally, mount ADC or set
# GOOGLE_APPLICATION_CREDENTIALS to a key file that is *not* inside the
# build context (see .dockerignore).

FROM python:3.12-slim AS base

# Vertex AI's video/image SDK calls need real TLS roots; slim images already
# ship ca-certificates, but keep it explicit and pin nothing else system-wide.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies in their own layer so code-only changes don't bust the
# pip cache.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Only what the server actually needs at runtime — not scripts/, tests/,
# docs/, web/, guides/, competitions/, or any devlog content.
COPY mcp_server/ ./mcp_server/
COPY src/media_gen/ ./src/media_gen/
COPY projects/registry.json ./projects/registry.json

# Cloud Run runs containers as a non-root user by convention; do the same
# locally so behavior matches.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Cloud Run injects PORT; __main__.py reads it (default 8080 if unset, e.g.
# for `docker run` without -e PORT).
ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["python", "-m", "mcp_server"]
