# Steel Browser MCP deploy + acceptance automation

## Goal

Steel Browser MCPを、初回のGCP trust bootstrap後は次の流れで自動運用する。

`main merge -> GitHub Actions OIDC -> container build/push -> Cloud Run image update -> /readyz -> real 5-step acceptance`

受入工程:

1. `create_session(project_slug="rss7-ai-media")`
2. `navigate` → `https://example.com/`
3. `extract(format="text")`
4. `screenshot(full_page=false)`
5. `release_session`

## Security model

- GitHub Actions SecretsへGCPサービスアカウント鍵、`STEEL_API_KEY`、`STEEL_BROWSER_MCP_TOKEN`を保存しない。
- Google Cloudへの認証はGitHub Actions OIDC + Workload Identity Federation (WIF)を使う。
- WIF providerは次を条件に固定する:
  - repository: `oosaka0123-sudo/ai-agent`
  - ref: `refs/heads/main`
  - workflow_ref: `oosaka0123-sudo/ai-agent/.github/workflows/steel-browser-acceptance.yml@refs/heads/main`
  - event: `push` または `workflow_dispatch`
- GitHub deployer SAは `github-actions-steel-deployer@rss7-ai-media.iam.gserviceaccount.com`。
- deployerにはArtifact Registry Writer、Cloud Run Developer、Service Usage Consumer、およびSteel runtime SAに対するService Account Userだけを付与する。
- Cloud Runの`POST /acceptance`はMCP Bearer tokenとは別系統でGitHub OIDCを検証する。
- application acceptance JWTはGitHub JWKS + RS256で検証し、repository/ref/workflow_ref/event/audienceをfail-closedで固定照合する。
- レスポンスにsession ID、Steel API Key、MCP token、screenshot base64本体を含めない。
- `gha-creds-*.json` は`.gitignore`と`.dockerignore`の両方で除外する。

## One-time bootstrap

WIF trustはGCP側へ一度だけ作る必要がある。GCP認証済みCloud Shellで次の1行を実行する。

```bash
curl -fsSL https://raw.githubusercontent.com/oosaka0123-sudo/ai-agent/main/scripts/bootstrap_steel_github_wif.sh -o /tmp/bootstrap-steel-wif.sh && bash /tmp/bootstrap-steel-wif.sh
```

このbootstrapはSecret値を表示せず、以下を連続実行する。

1. GitHub deployer service account作成（存在すれば再利用）
2. Workload Identity Pool / Provider作成
3. repository/main/workflow/event条件をproviderへ設定
4. 最小限のdeploy権限を付与
5. `ai-agent/main`を最新化
6. `scripts/redeploy_steel_browser_mcp.sh`で現行mainをSteel Cloud Runへ再デプロイ
7. `scripts/run_steel_acceptance_cloudshell.sh`で実5工程を実行

したがって、この一度のbootstrapで現在のIssue #44の最終受入も実行できる。

## Automatic workflow

`.github/workflows/steel-browser-acceptance.yml` は、Steel runtimeに影響するファイルが`main`へpushされた場合と、手動`workflow_dispatch`で動く。

Actions側は:

1. GitHub OIDCからWIF経由で短期GCP credentialsを取得
2. GitHub runner上で`Dockerfile.steel-browser`をbuild
3. `us-central1-docker.pkg.dev/rss7-ai-media/cloud-run-source-deploy/steel-browser-mcp:<commit SHA>`へpush
4. 既存`steel-browser-mcp`サービスのimageだけを更新（Secret/env/runtime SA設定を上書きしない）
5. `/readyz`を確認
6. application acceptance用の別GitHub OIDC tokenを取得
7. `POST /acceptance`で5工程を実行

## Manual fallback

自動デプロイ経路に障害がある場合だけ、GCP認証済み環境の最新`main`で:

```bash
bash scripts/redeploy_steel_browser_mcp.sh
bash scripts/run_steel_acceptance_cloudshell.sh
```

を使う。通常運用では不要。

## Success criteria

実環境で次を満たした場合のみIssue #44をcloseする。

- `/readyz` = HTTP 200 / `ready=true`
- `create_session` PASS
- `navigate` PASS
- `extract` PASS
- `screenshot` PASS
- `release_session` PASS
- acceptance result = `ALL_PASS`
