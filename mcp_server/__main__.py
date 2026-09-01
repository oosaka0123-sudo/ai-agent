"""Local dev / Cloud Run entrypoint: `python -m mcp_server`.

Cloud Run sets `PORT` and expects the container to listen on `0.0.0.0` on
that port — both handled here rather than baked into the Dockerfile, so the
same image works locally with a different port if needed.
"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("mcp_server.app:app", host="0.0.0.0", port=port, log_config=None)


if __name__ == "__main__":
    main()
