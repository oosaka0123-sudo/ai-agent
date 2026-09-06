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

The following manual operations are required by a human operator and cannot be completed automatically in the codebase (billing / credential creation — see `AGENTS.md`'s autonomous-execution exceptions).

**Important — do not use `--source=.` alone.** Both MCP servers in this
repository live under the same `mcp_server/` package, and `gcloud run
deploy --source=.` always builds whatever `Dockerfile` sits at the repo
root, which is the *unrelated* Google Media MCP server
(`mcp_server.app:app`). Steel Browser MCP has its own `Dockerfile.steel-browser`
(root of this repo) and `cloudbuild.steel-browser.yaml`, and must be built
with those explicitly — the commands below already do this, and have been
verified locally (dependency install → `uvicorn mcp_server.steel_app:app` →
`/healthz` and `/readyz` both returned `200`).

### スマホから実行する場合（推奨: Google Cloud Shell）

PCなしでこの節を実施する最短経路は **Google Cloud Shell**（ブラウザだけで動くLinuxターミナル。
スマホのブラウザからも `https://console.cloud.google.com` を開き、画面上部の
Cloud Shellアイコン（`>_`）をタップすると起動する。gcloudは自分のGoogleアカウントで
ログイン済みの状態で使える）を使うこと。ローカルPC・GitHub Actions・Docker Desktop等は不要。

1. **必要なAPIを有効化する**（初回のみ。既に有効な場合はこのコマンドは何もしない。
   無料枠の範囲内: Cloud Run・Cloud Build・Artifact Registry・Secret Managerはいずれも
   毎月の無料枠がある）:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
     artifactregistry.googleapis.com secretmanager.googleapis.com \
     --project=<your-gcp-project>
   ```
2. **Steel API Keyを取得する**: ブラウザで `https://steel.dev` を開き、アカウント登録後、
   ダッシュボードからAPI Keyを取得する（値は控えておくが、どこにも貼り付けない）。
3. **Cloud Shellを開く**: `https://console.cloud.google.com` をスマホのブラウザで開き、
   対象プロジェクト（例: `rss7-ai-media`）を選択し、画面上部の `>_` アイコンをタップする。
4. **このリポジトリをCloud Shellへ取得する**:
   ```bash
   git clone https://github.com/oosaka0123-sudo/ai-agent.git
   cd ai-agent
   ```
5. **Steel API Keyをシークレット登録する**（値は貼り付け後、画面から消える。コミット・ログには残らない）:
   ```bash
   printf '%s' "ここに取得したSteel API Keyを貼り付け" | \
     gcloud secrets create steel-api-key --data-file=- --project=<your-gcp-project>
   ```
6. **MCPエンドポイント自体を守るトークンを生成し、シークレット登録する**:
   ```bash
   openssl rand -hex 32 | tee /tmp/steel-mcp-token.txt
   gcloud secrets create steel-mcp-token --data-file=/tmp/steel-mcp-token.txt --project=<your-gcp-project>
   shred -u /tmp/steel-mcp-token.txt 2>/dev/null || rm -f /tmp/steel-mcp-token.txt
   ```
   （表示された値は、後でAIクライアント側のMCP設定に使うので、この時だけ控えておく）
7. **`Dockerfile.steel-browser` を使ってビルド・デプロイする**（`cloudbuild.steel-browser.yaml` が
   ビルド対象を正しいDockerfileに固定するので、誤って別サービスをビルドしない）:
   ```bash
   PROJECT_ID=<your-gcp-project>
   REGION=us-central1
   IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/steel-browser-mcp:latest"

   gcloud artifacts repositories create cloud-run-source-deploy \
     --repository-format=docker --location="$REGION" --project="$PROJECT_ID" \
     2>/dev/null || true  # 既に存在する場合はエラーを無視してよい

   gcloud builds submit --config=cloudbuild.steel-browser.yaml \
     --substitutions=_IMAGE="$IMAGE" --project="$PROJECT_ID" .

   gcloud run deploy steel-browser-mcp \
     --project="$PROJECT_ID" --region="$REGION" \
     --image="$IMAGE" \
     --allow-unauthenticated \
     --set-env-vars=STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES=10 \
     --set-secrets=STEEL_API_KEY=steel-api-key:latest,STEEL_BROWSER_MCP_TOKEN=steel-mcp-token:latest
   ```
   `--allow-unauthenticated` はCloud Run自体のIAM認証を無効化するが、アプリ側の
   `STEEL_BROWSER_MCP_TOKEN`（Bearer認証）は必須のまま — Claude Code等のAIクライアントは
   通常Google IDを持たないため、この組み合わせが実用的な既定値（Google Media MCPと同じ考え方）。
8. **デプロイ後に表示されるService URL（例: `https://steel-browser-mcp-xxxxx-uc.a.run.app`）を控え、
   ホスト名だけを許可リストへ設定する**:
   ```bash
   gcloud run services update steel-browser-mcp --region="$REGION" --project="$PROJECT_ID" \
     --update-env-vars=STEEL_BROWSER_MCP_ALLOWED_HOSTS=steel-browser-mcp-xxxxx-uc.a.run.app
   ```
   （`steel-browser-mcp-xxxxx-uc.a.run.app` は実際のURLのホスト名部分に置き換える。
   これを設定するまで `/readyz` は `503` を返し続ける — 意図した fail-closed 動作）。
9. **到達性を確認する**（このリポジトリの `.github/workflows/mcp-connectivity-check.yml` を
   GitHub Actionsタブから `workflow_dispatch` で実行し、`steel_browser_mcp_url` 入力欄へ
   このService URLを貼り付けると、GitHub Actions側からも `/healthz` `/readyz` を確認できる）:
   ```bash
   curl https://steel-browser-mcp-xxxxx-uc.a.run.app/healthz
   curl https://steel-browser-mcp-xxxxx-uc.a.run.app/readyz
   ```
10. **AIクライアント側にMCPエンドポイントを登録する**:
   - Claude Code / ChatGPT / Custom GPT等のMCP設定で、URLに `https://<Service URL>/mcp`、
     `Authorization` ヘッダーに `Bearer <手順5で控えたトークン>` を設定する。
   - このリポジトリ自身から使う場合は、`.mcp.json` の `mcpServers` に
     `google-media` と同じ形（`headers.Authorization` を `${STEEL_BROWSER_MCP_TOKEN}` という
     環境変数参照にする）で `steel-browser` エントリを追加する（実値は書かない）。
