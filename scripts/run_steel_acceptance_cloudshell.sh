#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ID="${PROJECT_ID:-rss7-ai-media}"
REGION="${REGION:-us-central1}"
SERVICE="${STEEL_BROWSER_SERVICE:-steel-browser-mcp}"
TARGET_URL="${STEEL_BROWSER_TEST_URL:-https://example.com/}"

for cmd in gcloud python3 curl; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "[FAIL] required command not found: $cmd" >&2
    exit 1
  }
done

echo "[1/6] Resolving Steel Browser canonical Cloud Run URL..."
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
if [[ -z "$PROJECT_NUMBER" ]]; then
  echo "[FAIL] Google Cloud project number could not be resolved." >&2
  exit 1
fi
BASE_URL="${STEEL_BROWSER_BASE_URL:-https://${SERVICE}-${PROJECT_NUMBER}.${REGION}.run.app}"
BASE_URL="${BASE_URL%/}"
MCP_URL="${BASE_URL}/mcp/"
echo "[PASS] service resolved: $BASE_URL"

echo "[2/6] Checking readiness..."
READY_BODY="$(curl -fsS --connect-timeout 10 --max-time 20 "${BASE_URL}/readyz")"
if [[ "$READY_BODY" != *'"ready":true'* && "$READY_BODY" != *'"ready": true'* ]]; then
  echo "[FAIL] /readyz did not report ready=true: $READY_BODY" >&2
  exit 1
fi
echo "[PASS] /readyz ready=true"

echo "[3/6] Reading MCP bearer token from Secret Manager..."
STEEL_BROWSER_MCP_TOKEN="$(gcloud secrets versions access latest \
  --secret=steel-mcp-token \
  --project="$PROJECT_ID")"
if [[ -z "$STEEL_BROWSER_MCP_TOKEN" ]]; then
  echo "[FAIL] steel-mcp-token was empty." >&2
  exit 1
fi
export STEEL_BROWSER_MCP_TOKEN MCP_URL PROJECT_ID TARGET_URL
# Never print the token.
echo "[PASS] token loaded without displaying its value"

TMP_DIR="$(mktemp -d)"
cleanup() {
  unset STEEL_BROWSER_MCP_TOKEN MCP_URL PROJECT_ID TARGET_URL
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "[4/6] Preparing isolated MCP client..."
python3 -m venv "$TMP_DIR/venv"
"$TMP_DIR/venv/bin/python" -m pip install --quiet --disable-pip-version-check 'mcp[cli]>=2.0.0,<3'
echo "[PASS] MCP Python client ready"

echo "[5/6] Running authenticated browser lifecycle..."
"$TMP_DIR/venv/bin/python" - <<'PY'
import asyncio
import json
import os

from mcp import Client
from mcp.client.streamable_http import httpx2, streamable_http_client

MCP_URL = os.environ["MCP_URL"]
TOKEN = os.environ["STEEL_BROWSER_MCP_TOKEN"]
PROJECT_ID = os.environ["PROJECT_ID"]
TARGET_URL = os.environ["TARGET_URL"]
REQUIRED_TOOLS = {"create_session", "navigate", "extract", "screenshot", "release_session"}


def unpack(result, tool_name):
    if bool(getattr(result, "is_error", False)):
        raise RuntimeError(f"{tool_name} returned isError=true")

    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured

    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, dict):
            return decoded

    raise RuntimeError(f"{tool_name} returned no structured dictionary payload")


async def run():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    timeout = httpx2.Timeout(30.0, read=300.0)

    async with httpx2.AsyncClient(headers=headers, timeout=timeout) as http_client:
        transport = streamable_http_client(MCP_URL, http_client=http_client)
        async with Client(transport) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            missing = REQUIRED_TOOLS - names
            if missing:
                raise RuntimeError(f"MCP connected but required tools are missing: {sorted(missing)}")
            print(f"[PASS] MCP connected; 5 required tools are available")

            session_id = None
            primary_error = None
            try:
                created = unpack(
                    await client.call_tool(
                        "create_session",
                        {"project_slug": PROJECT_ID},
                    ),
                    "create_session",
                )
                session_id = created.get("session_id")
                if not session_id:
                    raise RuntimeError("create_session returned no session_id")
                print("[PASS] create_session")

                navigated = unpack(
                    await client.call_tool(
                        "navigate",
                        {"session_id": session_id, "url": TARGET_URL},
                    ),
                    "navigate",
                )
                if navigated.get("status") != "success":
                    raise RuntimeError(f"navigate returned unexpected status: {navigated.get('status')}")
                print("[PASS] navigate")

                extracted = unpack(
                    await client.call_tool(
                        "extract",
                        {"session_id": session_id, "format": "text"},
                    ),
                    "extract",
                )
                text = extracted.get("content") or ""
                if not text.strip():
                    raise RuntimeError("extract returned empty content")
                print(f"[PASS] extract ({len(text)} chars)")

                captured = unpack(
                    await client.call_tool(
                        "screenshot",
                        {"session_id": session_id, "full_page": False},
                    ),
                    "screenshot",
                )
                image_b64 = captured.get("screenshot_base64") or ""
                if len(image_b64) < 100:
                    raise RuntimeError("screenshot returned no usable PNG payload")
                if captured.get("mime_type") != "image/png":
                    raise RuntimeError(f"unexpected screenshot mime_type: {captured.get('mime_type')}")
                print(f"[PASS] screenshot ({len(image_b64)} base64 chars; payload not printed)")
            except Exception as exc:
                primary_error = exc
            finally:
                if session_id:
                    try:
                        released = unpack(
                            await client.call_tool(
                                "release_session",
                                {"session_id": session_id},
                            ),
                            "release_session",
                        )
                        if released.get("status") != "released":
                            raise RuntimeError(
                                f"release_session returned unexpected status: {released.get('status')}"
                            )
                        print("[PASS] release_session")
                    except Exception as release_exc:
                        if primary_error is None:
                            primary_error = release_exc
                        else:
                            print(f"[WARN] release_session also failed: {type(release_exc).__name__}: {release_exc}")

            if primary_error is not None:
                raise primary_error


asyncio.run(run())
PY

echo "[6/6] Steel Browser MCP acceptance test: ALL PASS"
