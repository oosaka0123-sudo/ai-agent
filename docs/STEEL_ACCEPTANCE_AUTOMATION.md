# Steel Browser MCP acceptance automation

## Goal

Cloud Shellへの手入力を受入試験の必須条件から外し、GitHub ActionsからSteel Browser MCPの実ブラウザ5工程を安全に実行する。

対象工程:

1. `create_session(project_slug="rss7-ai-media")`
2. `navigate` → `https://example.com/`
3. `extract(format="text")`
4. `screenshot(full_page=false)`
5. `release_session`

## Security model

- GitHub Actions側に`STEEL_API_KEY`や`STEEL_BROWSER_MCP_TOKEN`を保存しない。
- workflowは`id-token: write`でGitHub Actions OIDCの短期JWTを取得する。
- Cloud Runの`POST /acceptance`はMCP Bearer tokenとは別系統でGitHub OIDCを検証する。
- JWT署名はGitHubのJWKSを使いRS256で検証する。
- `iss` / `aud`に加えて以下を固定照合する:
  - `repository = oosaka0123-sudo/ai-agent`
  - `ref = refs/heads/main`
  - `workflow_ref = oosaka0123-sudo/ai-agent/.github/workflows/steel-browser-acceptance.yml@refs/heads/main`
  - `event_name = workflow_dispatch`
- 別repo・別branch・別workflowのGitHub OIDC tokenでは起動できない。
- レスポンスにsession ID、Steel API Key、MCP token、screenshot base64本体を含めない。
- 返す実行証跡は各stepのPASS/FAIL、extract文字数、screenshot base64文字数、MIME typeのみ。

## Workflow

`.github/workflows/steel-browser-acceptance.yml`

GitHub Actionsの`Run workflow`から起動する。既定のCloud Run base URLは:

`https://steel-browser-mcp-518404402696.us-central1.run.app`

service URLが変わった場合のみworkflow inputで上書きする。

## Initial deployment boundary

この機能を既存Steel Browser Cloud Runへ反映する最初の1回だけ、新revisionへの再デプロイが必要。その後の受入試験はCloud Shellへtokenやコマンドを貼らずGitHub Actionsから実行できる。

## Success criteria

workflowがHTTP 200を受け、レスポンスが次を満たすこと:

- `ok: true`
- `result: ALL_PASS`
- 5工程が上記順序で全て`status: pass`

この条件を実環境で確認した後にのみIssue #44をcloseする。
