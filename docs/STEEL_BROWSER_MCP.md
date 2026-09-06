# Steel Browser MCP — Architecture, Setup, and Operations

Shared Remote HTTP MCP exposing Steel Cloud Browser capability to AI clients (ChatGPT, Claude, Gemini, etc.) as a common control plane infrastructure.

## Architecture

```
AI Clients (ChatGPT / Claude / Gemini / etc.)
        │  calls Remote HTTP MCP
        │  Header: Authorization: Bearer <STEEL_BROWSER_MCP_TOKEN>
        ▼
Steel Browser Remote HTTP MCP  (mcp_server/steel_browser/, this repository)
        │  Inbound Bearer Token Auth
        │  URL SSRF & Private IP Validation
        │  Session Tracker (TTL, idle cleanup)
        ▼
Steel Cloud Browser Upstream API  (https://api.steel.dev)
        │  Authenticated with STEEL_API_KEY (Server Secret only)
        ▼
Browser Session Lifecycle (create -> navigate -> extract/screenshot -> release)
```

### Key Security & Cost Design Decisions

1. **Auth Separation**:
   - Inbound authentication (`STEEL_BROWSER_MCP_TOKEN`) gates client calls to the MCP endpoint.
   - Upstream authentication (`STEEL_API_KEY`) is stored **only** as a server-side secret on Cloud Run / environment. MCP clients never receive or handle the Steel API key.
2. **SSRF & Private Network Defense**:
   - All navigation targets in `navigate`, `extract`, and `screenshot` undergo mandatory URL validation (`url_validator.py`).
   - Blocks non-HTTP/HTTPS schemes, `localhost`, `127.0.0.1`, `::1`, `0.0.0.0`, cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`), and RFC1918 private IPv4/IPv6 ranges.
   - `extract` and `screenshot` require an explicit validated URL until the session has successfully navigated to an HTTP(S) page. There is no `about:blank` fallback.
3. **Cost Safety & Session TTL Cleanup**:
   - In-memory `SessionTracker` tracks creation and last-activity timestamps for every active session.
   - Background cleanup task automatically releases sessions exceeding inactivity (`STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES`, default 10m) or maximum lifetime (`STEEL_BROWSER_SESSION_MAX_TIMEOUT_MINUTES`, default 30m).
   - Explicit TTL values must be positive integers, and maximum lifetime must be greater than or equal to inactivity timeout.
   - Application shutdown (`lifespan`) automatically executes `release_all` to prevent dangling browser sessions from incurring charges.
4. **Fail-closed Readiness**:
   - `/readyz` returns `503` unless `STEEL_API_KEY`, `STEEL_BROWSER_MCP_TOKEN`, and at least one explicit `STEEL_BROWSER_MCP_ALLOWED_HOSTS` value are configured and timeout values are valid.

## Available MCP Tools

1. **`create_session`**
   - Creates a new Steel cloud browser session.
   - Parameters: `project_slug` (required, e.g. `"my-project"`), `session_id` (optional), `use_proxy` (bool), `solve_captcha` (bool).
   - Returns: `session_id`, `status`, `created_at`, `debug_url`, `project_slug`.
2. **`navigate`**
   - Navigates an active session to a validated HTTP(S) URL.
   - Parameters: `session_id` (required), `url` (required).
   - Returns: `session_id`, `url`, `title`, `status`.
3. **`extract`**
   - Extracts page content in `markdown`, `html`, or plain `text` format.
   - Parameters: `session_id` (required), `url` (optional only after successful validated navigation), `format` (default `"markdown"`).
   - Returns: `session_id`, `url`, `format`, `content`.
4. **`screenshot`**
   - Captures a base64-encoded PNG screenshot of the session page.
   - Parameters: `session_id` (required), `url` (optional only after successful validated navigation), `full_page` (bool).
   - Returns: `session_id`, `url`, `screenshot_base64`, `mime_type`.
5. **`release_session`**
   - Explicitly closes and releases the Steel browser session.
   - Parameters: `session_id` (required).
   - Returns: `session_id`, `status`.

## Environment Variables

| Variable Name | Description | Required | Default |
|---|---|---|---|
| `STEEL_API_KEY` | Upstream Steel API Key for cloud browser creation and execution. | Yes | None |
| `STEEL_BROWSER_MCP_TOKEN` | Bearer token required for clients calling the Remote HTTP MCP endpoint. | Yes | None |
| `STEEL_BROWSER_MCP_ALLOWED_HOSTS` | Comma-separated list of explicit allowed host headers for DNS rebinding protection. | Yes | None |
| `STEEL_BROWSER_MCP_ALLOWED_ORIGINS` | Comma-separated list of allowed origin headers. | Optional | Empty |
| `STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES` | Maximum minutes a session can remain idle before auto-release. Must be a positive integer if set. | No | `10` |
| `STEEL_BROWSER_SESSION_MAX_TIMEOUT_MINUTES` | Maximum total lifetime minutes for a browser session. Must be a positive integer and >= inactivity timeout if set. | No | `30` |

## Local Development & Running

To run locally with uvicorn:
```bash
export STEEL_API_KEY="your-steel-api-key"
export STEEL_BROWSER_MCP_TOKEN="your-mcp-bearer-token"
export STEEL_BROWSER_MCP_ALLOWED_HOSTS="localhost,127.0.0.1"

uvicorn mcp_server.steel_app:app --host 0.0.0.0 --port 8000
```

Health check endpoints:
- `GET /healthz` -> Returns `200 OK` (`ok`)
- `GET /readyz` -> Returns `200 OK` (`{"ready": true}`) only when required fail-closed configuration is valid; otherwise `503 Service Unavailable`.

---

## Human Gate Instructions

The following manual operations are required by a human operator and cannot be completed automatically in the codebase:

1. **Steel API Key & Cloud Secret Registration**:
   - Obtain a Steel API Key from `https://steel.dev`.
   - Register `STEEL_API_KEY` in Google Secret Manager or Cloud Run Environment Variables:
     ```bash
     gcloud secrets create steel-api-key --data-file=- --project=<your-gcp-project>
     ```
2. **Cloud Run Deployment & IAM**:
   - Deploy the container to Google Cloud Run:
     ```bash
     gcloud run deploy steel-browser-mcp \
       --project=<your-gcp-project> --region=us-central1 \
       --source=. \
       --set-env-vars=STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES=10 \
       --set-secrets=STEEL_API_KEY=steel-api-key:latest,STEEL_BROWSER_MCP_TOKEN=steel-mcp-token:latest
     ```
   - Record the deployed Cloud Run service URL and set `STEEL_BROWSER_MCP_ALLOWED_HOSTS` to the explicit service hostname before considering the service ready.
3. **ChatGPT / AI Client Registration**:
   - In ChatGPT / Custom GPT / Claude Client settings, register a Remote HTTP MCP Endpoint pointing to `https://<your-cloud-run-url>/mcp`.
   - Set the `Authorization` header to `Bearer <STEEL_BROWSER_MCP_TOKEN>`.
