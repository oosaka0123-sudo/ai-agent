# Mobile First / Cloud First

更新日: 2026-09-06（GitHub Actions経由でCloud Run自体の正常稼働を確認）

ユーザーの明示的な方針決定により、**Mobile First / Cloud First**
（原則としてユーザーがスマートフォンだけから「指示 → AI作業 → GitHub変更 →
テスト → 承認 → デプロイ」まで完結できる環境を目指す）を、このリポジトリでも
共通原則として扱う。

Master側の正本は `oosaka0123-sudo/ai-master` の `DECISIONS.md`（ADR-015）と
`AGENTS.md`（DEFAULT項目13）。既存のADR-013（PC電源OFF運用はGitHub Actions/API優先）
を否定・置換するものではなく、その適用範囲を開発ライフサイクル全体へ拡張したもの。
`docs/CLAUDE_FAMILY_ROLES.md` の役割分担・MCP分類とあわせて読むこと。

この文書は、Masterの共通原則をこの `ai-agent` リポジトリの実態に照らして
棚卸しし、スマホ完結を阻害するローカル依存箇所と推奨構成を記録する
Projectローカルの実装ドキュメント。Masterへは進捗をコピーしない
（`ai-master/DECISIONS.md` ADR-015 Impact参照）。

## 棚卸し表

`機能 | 現在 | スマホ完結 | 問題 | 推奨構成 | 次の作業`

| 機能 | 現在 | スマホ完結 | 問題 | 推奨構成 | 次の作業 |
|---|---|---|---|---|---|
| Claude（chat） | claude.aiのWeb/モバイルアプリから利用可能 | ✅ 完結 | 特になし | 現状維持 | なし |
| Claude Code（実行環境） | 本セッションはClaude Code on the web（クラウド実行環境）で稼働中。ローカルデスクトップCLIも利用可能だが必須ではない | ✅ クラウド実行を使えば完結 | ローカルCLI版を使う場合はPC依存が発生する | 原則クラウド実行（Claude Code on the web）を使う。ローカルCLIはオフライン作業等の補助手段と位置づける（ADR-015 item3） | なし |
| Claude Cowork | 本セッション（Claude Code）からは実接続・実能力を確認できていない（UNKNOWN） | 未確認（製品としてはクラウドサービス想定のため理論上は可能） | このセッションにCoworkへの実アクセス手段がなく、live evidenceがない | Coworkをクラウドオーケストレーターとして使う（ADR-015 item4） | Claude Coworkの実セッションで接続を確認し、`ai-master/CONNECT.md` へ実アクセスの結果を追記する（本タスクの範囲外） |
| GitHub操作（Repository / PR / Actions） | GitHub MCP経由でClaude Codeから実行可能。GitHub公式モバイルアプリからもPRレビュー・承認・マージ可能 | ✅ 完結（本タスクで実際にPR作成・レビュー対応・マージ可能状態までクラウドのみで完了した） | 特になし | 現状維持 | なし |
| Google Media MCP（画像・動画生成） | **Cloud Runサービス自体は生きていることを確認済み。** GitHub Actions（`mcp-connectivity-check.yml`、Claude Codeのegress制約を経由しない）から`/readyz`を2回実行し、いずれも`200 {"ready":true}`（アプリ自身が返す実レスポンス）を確認した。`/readyz`（`mcp_server/app.py`の`_readyz`→`get_server_config()`）は`GOOGLE_CLOUD_PROJECT`・`GOOGLE_MEDIA_GCS_BUCKET`・サーバー側`GOOGLE_MEDIA_MCP_TOKEN`が設定済みであることしか検証しない。**IAM権限・API有効化・`GOOGLE_MEDIA_MCP_ALLOWED_HOSTS`の設定はこの結果だけでは未確認のまま**（Copilotレビュー指摘により表現を訂正）。一方 `/healthz` は同じ2回とも`404`（Googleの汎用エラーページ、アプリの応答ではない）で、原因は未特定（下記参照）。**このClaude Code実行環境からの接続のみ**が、`GOOGLE_MEDIA_MCP_TOKEN`未設定とegress policy拒否によりブロックされている | ⚠️ Cloud Runサービス自体は生存確認済みだが、IAM/API有効化/許可ホストは未検証。この実行環境からの接続は未完結 | (1) この実行環境のegress policyがCloud Runホストを許可していない（環境設定の問題。コード側では解決不可） (2) `GOOGLE_MEDIA_MCP_TOKEN` が本実行環境に未設定（環境変数の問題。コード側では解決不可） (3) `/healthz`だけがGoogle側の汎用404を返す原因不明の現象（`/readyz`は正常。MCP呼び出し自体は`/mcp`エンドポイントを使うため実用上のブロッカーではないが要調査） (4) IAM権限・API有効化・許可ホスト設定は`/readyz`では検証されず未確認 | Remote HTTP MCP構成自体は維持する（ADR-015と整合）。(1)(2)とも環境設定側の変更で解消する、コード修正は不要。(3)は人間がCloud Runのingress/ロードバランサー設定を確認。(4)は実際に`generate_image`等を呼んで初めて確認できる | 今回 `.mcp.json` をこのリポジトリ直下へ追加し、GitHub Actions経由でCloud Runサービス自体の到達性を実証した。(1)(2)の具体的な設定手順は下記「切り分け結果」参照 |
| Steel Browser MCP（クラウドブラウザ） | 実装済みだがCloud Runへの実デプロイは未実施。**コード側のブロッカーを発見・修正した**: `gcloud run deploy --source=.` は常にリポジトリ直下の `Dockerfile`（無関係のGoogle Media MCP用）を拾ってしまい、Steel Browser MCPを正しくデプロイできない構成になっていた。専用の `Dockerfile.steel-browser` と `cloudbuild.steel-browser.yaml` を追加し、ローカルで依存関係インストール→起動→`/healthz`・`/readyz`が200を返すことまで確認した（実際のデプロイはCloud Run/gcloud認証情報がこの環境にないため未実施） | ❌ 未完結（稼働中のエンドポイントが存在しない。コード側の準備は完了） | 実デプロイには人間の操作が必要（Human Gate: gcloud認証・課金確認） | デプロイ自体はADR-015に沿ってCloud Run（Remote HTTP MCP）で行う。PCを使わず**Google Cloud Shell**（ブラウザだけで動くターミナル、スマホ対応）から実行できる手順を用意した | `docs/STEEL_BROWSER_MCP.md`「Human Gate Instructions」の手順（APIの有効化 → Steel API Key取得 → Cloud Shellでclone → Secret登録 → `cloudbuild.steel-browser.yaml`でビルド・デプロイ → 許可ホスト設定 → 到達性確認 → AIクライアント登録）を人間が実施する |
| メディア生成CLI（`scripts/generate_media.py`） | Claude Codeのクラウド実行環境内でPythonスクリプトとして実行可能（ローカルPC不要）。ただしGoogle Cloud認証（ADC）の初回セットアップが必要 | △ 部分的（クラウド実行環境内では動くが、初回のgcloud認証セットアップに手間がかかる） | Google Media MCPが使えない間は、このCLIが唯一の生成手段になり認証セットアップの手間が残る | 通常利用はGoogle Media MCP経由に一本化し、CLIは開発者向けデバッグ手段として位置づける（既に `docs/GOOGLE_MEDIA_MCP.md` に同種の位置づけあり） | なし（Google Media MCP接続が復旧すればこの経路への依存は自然に下がる） |
| テスト・CI（pytest / gitleaks） | `.github/workflows/ci.yml` でPRごとに自動実行、GitHub Actions（クラウド）で完結 | ✅ 完結（本PRで実際にCI緑を確認済み） | 特になし | 現状維持 | なし |
| サイトデプロイ（GitHub Pages） | `main` へのpushで `.github/workflows/pages.yml` が自動デプロイ | ✅ 完結 | 特になし | 現状維持 | なし |
| 定型運用（GPT Ops / Register Site / Auto Site Onboarding / Client Repo Factory） | すべてGitHub Actionsベース。ChatGPTは `.gpt-ops/command.txt` の更新だけで `deploy-pages` / `health-check` を実行可能（既存のスマホ完結設計の先行実例） | ✅ 完結（既存の先行実例） | Claude Cowork / Claude Code向けの同等の定型操作の仕組みは未整備 | 「ファイル更新 → GitHub Actionsトリガー」という同じパターンを、Cowork/Claude Codeの定型操作へも展開できないか検討する | 追加するかはユーザー判断待ち（本タスクの範囲外） |
| Secret管理 | `.env` はローカル/デプロイ環境変数用、`.env.example` はキー名のみ。Cloud Run側はSecret Manager/環境変数、GitHub Actionsは `secrets.GITHUB_TOKEN` 等のGitHub Secretsを使用 | ✅ 設計としては完結（値そのものをリポジトリへ置かない設計が既に徹底されている） | 本タスクの範囲で新たな秘密値の露出は発見していない | 現状維持（ADR-015 item8と整合） | なし |

## 切り分け結果: Google Media MCPのHTTP 403（コード側か環境側か）

2026-09-06に、Claude Code cloud実行環境から2つの独立した確認を実施し、
**コード側（`mcp_server/`・Cloud Run・Google Cloud側の設定）の問題ではなく、
この実行環境（Claude Code on the webのenvironment設定）側の問題である**と切り分けた。

### 確認1: egress policyによるCONNECT拒否

```
curl https://google-media-mcp-518404402696.us-central1.run.app/healthz
→ curl: (56) CONNECT tunnel failed, response 403
```

agent proxyのステータスエンドポイント（`$HTTPS_PROXY/__agentproxy/status`）の
`recentRelayFailures` は次を記録した。

```json
{"kind": "connect_rejected", "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)",
 "host": "google-media-mcp-518404402696.us-central1.run.app:443"}
```

CONNECTメソッドへの403は、TLSトンネルを確立する**前**にproxy自身が拒否する応答であり、
Cloud Run（トンネル確立後のTLS/HTTPアプリケーション層）が返せる種類の応答ではない。
`/root/.ccr/README.md`（agent proxyの説明書）も「403/407はこのセッションの組織egress policyが
宛先ホストを許可していないことを意味する。リトライや回避を試みず、ブロックされたホストを報告する」と
明記している。よって、この403は **Cloud Run側・MCPサーバーのコード側の問題ではなく、
この実行環境自体のegress policy設定の問題**と判断できる。

### 確認2: 認証トークン未設定

```
$ [ -n "${GOOGLE_MEDIA_MCP_TOKEN:-}" ] && echo set || echo not set
not set
```

`.mcp.json` の `google-media` エントリが参照する `${GOOGLE_MEDIA_MCP_TOKEN}` が、
この実行環境の環境変数として設定されていないことを確認した（値の中身は一切表示・記録していない）。

### この実行環境の識別情報（OBSERVED）

- Environment名: `Default`（`environment_id: env_01CYPndo4QJ8xTExPzhz5asg`）
- Environment説明: `Default - trusted network access`
- この情報は `Claude_Code_Remote` MCPサーバーの `get_session` / `list_environments` から取得した
  （このセッション自身のメタデータ。秘密情報は含まない）。

### 人間が行うべき設定（1つずつ）

コード側の変更は不要。以下はいずれもGitHub/リポジトリの外側、
Claude Code on the webの環境設定（<https://code.claude.com/docs/en/claude-code-on-the-web>
に説明がある「environmentのnetwork policy」「環境変数」の設定）で行う。

1. **network policyの変更**: 上記environment（`Default` / `env_01CYPndo4QJ8xTExPzhz5asg`）の
   「trusted network access」ポリシーでは `google-media-mcp-518404402696.us-central1.run.app`
   への到達が拒否される。この環境の設定を編集して当該ホスト（または `*.run.app` のような
   Cloud Run全般）への到達を許可できるネットワークポリシーへ変更するか、そのような
   ポリシーを持つ新しいenvironmentを作成する。
2. **`GOOGLE_MEDIA_MCP_TOKEN` の設定**: 同じenvironmentの環境変数設定に、Google Media MCP
   サーバー側で発行済みのBearerトークン値を `GOOGLE_MEDIA_MCP_TOKEN` として登録する
   （トークン値そのものの発行・確認方法は [`docs/GOOGLE_MEDIA_MCP.md`](GOOGLE_MEDIA_MCP.md) 参照。
   Cloud Run側の設定を変更する場合は、そちらもあわせて確認する）。
3. **新しいセッションで確認**: 1・2の設定は既存の実行中セッションには反映されない
   （MCP設定・環境変数はセッション開始時に読み込まれるため）。設定変更後、`ai-agent` を
   対象に新しいClaude Code on the webセッションを開始し、`curl .../healthz` またはMCPツール
   一覧に `generate_image` / `generate_video` が現れるかで到達性を再確認する。
4. **（任意・当面の代替）Claude Cowork / claude.aiのコネクタ経由で試す**: このegress制約は
   Claude Code on the webのagent proxy固有のものであり、Claude Cowork・claude.ai本体の
   コネクタ経由の接続には適用されない可能性がある（未確認・HYPOTHESIS）。1〜3の設定変更を
   待たずに画像・動画生成だけを先に試したい場合、Claude Cowork側でGoogle Media MCPの
   接続を試すことも選択肢になる。

### GitHub Actions経由でのCloud Run到達性確認（追加確認、2026-09-06）

Claude Code cloud実行環境から到達できない項目（Cloud Run自体の生死、fail-closed設定の
妥当性）を補うため、`.github/workflows/mcp-connectivity-check.yml`
（GitHub-hosted runner、Claude Codeのegress制約を経由しない）から2回実行した。

- `/readyz`: 2回とも `200 {"ready":true}`（アプリ自身が返す実際のレスポンス）。
  → **Cloud Runサービス自体は生きており、起動している**。ただし`_readyz`の実装
  （`mcp_server/app.py` → `get_server_config()`）は `GOOGLE_CLOUD_PROJECT` /
  `GOOGLE_MEDIA_GCS_BUCKET` / サーバー側 `GOOGLE_MEDIA_MCP_TOKEN` が空でなく
  読み込めることしか検証しない。**IAM権限・API有効化（`aiplatform.googleapis.com`等）・
  `GOOGLE_MEDIA_MCP_ALLOWED_HOSTS`の設定はこの検証の対象外であり、この結果だけでは
  確認できていない**（初出時「間接的に問題なしと判断できる」と記載していたが誤りで、
  Copilotレビューの指摘により訂正した）。
- `/healthz`: 2回とも `404`（Googleの汎用エラーページ、アプリの`_healthz`ハンドラの
  応答ではない）。`/readyz`が同じホスト・同じアプリで正常に応答している以上、
  Cloud Runサービス自体が存在しないという意味ではない。原因はCloud Run手前の
  ingress/ロードバランサー設定等の可能性があるが、この棚卸しの範囲では特定できなかった
  （HYPOTHESIS）。MCP呼び出し自体は`/mcp`エンドポイントを使うため、この現象自体は
  実際のツール呼び出しをブロックしないと考えられるが、人間による調査を推奨する。

これにより、**チェックリストの1（Cloud Run正常性）は「サービス自体は生存」まで確認できた**。
2（MCP endpoint正常性）は`/readyz`のみ確認、`/mcp`自体は未確認。**5（IAM）・6（API有効化）は
`/readyz`では検証されないため、依然として未確認**。実際にIAM・API有効化まで確認するには
`generate_image`等のツールを実際に呼び出す必要があり、それはこのClaude Code実行環境からの
接続が確立してから初めて可能になる。残るブロッカーは4（このClaude Code実行環境からの
egress拒否）と、client側の`GOOGLE_MEDIA_MCP_TOKEN`未設定である。

## 今回実装したこと

- `.mcp.json`（リポジトリ直下、新規）: Google Media MCPの `google-media` エントリを追加した。
  URLはCloud Runの公開エンドポイント（既に `ai-master/CONNECT.md` で公開情報として記録済み）、
  認証は `${GOOGLE_MEDIA_MCP_TOKEN}` という環境変数参照のみで、実際のトークン値はこの
  ファイルにもリポジトリのどこにも含めていない（`scripts/onboard_projects.py` が他プロジェクトへ
  配布する際と同じ安全なパターンを踏襲）。
- `.github/workflows/mcp-connectivity-check.yml`: GitHub Actions経由でCloud Run到達性を
  確認できるworkflowを追加し、実際に2回実行してCloud Run自体の正常性を確認した（上記）。
- `Dockerfile.steel-browser` / `cloudbuild.steel-browser.yaml`: Steel Browser MCPの
  デプロイを阻害していたコード側のバグを修正した（詳細は該当行・`docs/STEEL_BROWSER_MCP.md`参照）。

## 実装できなかったこと・人間の操作が必要な項目

1. **Claude Code cloud実行環境（`Default` / `env_01CYPndo4QJ8xTExPzhz5asg`）のnetwork policy変更**
   — 上記「切り分け結果」参照。コード側では解決できない。
2. **`GOOGLE_MEDIA_MCP_TOKEN` の当該環境への設定** — 上記「切り分け結果」参照。
3. **Steel Browser MCPのCloud Runデプロイ** — この実行環境にはgcloud CLI自体が存在せず、
   Google Cloudの認証情報も一切ない（`which gcloud`で確認済み）ため、コード側では
   実行不可能。加えて課金を伴う人間承認が必要な操作（`AGENTS.md` 自律実行ルールの例外条件に
   該当）。コード側の準備（`Dockerfile.steel-browser`, `cloudbuild.steel-browser.yaml`,
   ローカルでの起動確認）は完了しており、`docs/STEEL_BROWSER_MCP.md` の手順（Google Cloud
   Shellから実行可能、PC不要）に従って人間が実施する。

これらは `AGENTS.md` の「未接続でも全体を停止しない」方針に従い、GitHub Issueまたは
今後のdevlog/引き継ぎで追跡し、全体の作業は停止しない。
