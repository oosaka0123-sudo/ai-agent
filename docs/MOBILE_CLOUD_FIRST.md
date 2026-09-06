# Mobile First / Cloud First

更新日: 2026-09-06

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
| Google Media MCP（画像・動画生成） | Cloud Run（`rss7-ai-media`）にデプロイ済み、Remote HTTP MCPとして公開URLあり。ただしこのClaude Code cloud実行環境からのCONNECTがagent proxyでHTTP 403（policy denial）として拒否されることを本日 `curl .../healthz` で再確認した（`ai-master/CONNECT.md`） | ❌ 現状未完結（Cloud Run自体はクラウド完結設計だが、実行環境からの経路がブロックされている） | (1) Claude Code cloud実行環境のegress policyがCloud Runホストを許可していない（AIエージェント側では解決不可、環境管理者・Anthropicサポート側の対応が必要） (2) client向け認証トークン（`GOOGLE_MEDIA_MCP_TOKEN`）が本実行環境の環境変数として設定済みか未確認 | Remote HTTP MCP構成自体は維持する（ADR-015と整合）。(1)は環境のegress許可設定、(2)はClaude Code実行環境のSecret/環境変数設定で解消する | 今回 `.mcp.json` をこのリポジトリ直下へ追加した（`google-media` エントリ、トークンは環境変数参照のみで実値は含まない）。(1)(2)は人間による環境設定が必要なため、GitHub Issueとして残すことを推奨する |
| Steel Browser MCP（クラウドブラウザ） | 実装済みだがCloud Runへの実デプロイは未実施（Human Gate: gcloud操作・課金が発生するため人間承認が必要）。現状ローカル起動でのみ動作確認可能 | ❌ 未完結（稼働中のエンドポイントが存在しない） | デプロイ未実施 | デプロイ自体はADR-015に沿ってCloud Run（Remote HTTP MCP）で行う。デプロイ操作は課金を伴うため引き続き人間承認が必要（`AGENTS.md` 自律実行ルールの例外） | 人間が `docs/STEEL_BROWSER_MCP.md` の手順でデプロイし、`STEEL_API_KEY` 等をCloud Run Secretへ登録する。デプロイ後、公開URLを `.mcp.json` へ追記する |
| メディア生成CLI（`scripts/generate_media.py`） | Claude Codeのクラウド実行環境内でPythonスクリプトとして実行可能（ローカルPC不要）。ただしGoogle Cloud認証（ADC）の初回セットアップが必要 | △ 部分的（クラウド実行環境内では動くが、初回のgcloud認証セットアップに手間がかかる） | Google Media MCPが使えない間は、このCLIが唯一の生成手段になり認証セットアップの手間が残る | 通常利用はGoogle Media MCP経由に一本化し、CLIは開発者向けデバッグ手段として位置づける（既に `docs/GOOGLE_MEDIA_MCP.md` に同種の位置づけあり） | なし（Google Media MCP接続が復旧すればこの経路への依存は自然に下がる） |
| テスト・CI（pytest / gitleaks） | `.github/workflows/ci.yml` でPRごとに自動実行、GitHub Actions（クラウド）で完結 | ✅ 完結（本PRで実際にCI緑を確認済み） | 特になし | 現状維持 | なし |
| サイトデプロイ（GitHub Pages） | `main` へのpushで `.github/workflows/pages.yml` が自動デプロイ | ✅ 完結 | 特になし | 現状維持 | なし |
| 定型運用（GPT Ops / Register Site / Auto Site Onboarding / Client Repo Factory） | すべてGitHub Actionsベース。ChatGPTは `.gpt-ops/command.txt` の更新だけで `deploy-pages` / `health-check` を実行可能（既存のスマホ完結設計の先行実例） | ✅ 完結（既存の先行実例） | Claude Cowork / Claude Code向けの同等の定型操作の仕組みは未整備 | 「ファイル更新 → GitHub Actionsトリガー」という同じパターンを、Cowork/Claude Codeの定型操作へも展開できないか検討する | 追加するかはユーザー判断待ち（本タスクの範囲外） |
| Secret管理 | `.env` はローカル/デプロイ環境変数用、`.env.example` はキー名のみ。Cloud Run側はSecret Manager/環境変数、GitHub Actionsは `secrets.GITHUB_TOKEN` 等のGitHub Secretsを使用 | ✅ 設計としては完結（値そのものをリポジトリへ置かない設計が既に徹底されている） | 本タスクの範囲で新たな秘密値の露出は発見していない | 現状維持（ADR-015 item8と整合） | なし |

## 今回実装したこと

- `.mcp.json`（リポジトリ直下、新規）: Google Media MCPの `google-media` エントリを追加した。
  URLはCloud Runの公開エンドポイント（既に `ai-master/CONNECT.md` で公開情報として記録済み）、
  認証は `${GOOGLE_MEDIA_MCP_TOKEN}` という環境変数参照のみで、実際のトークン値はこの
  ファイルにもリポジトリのどこにも含めていない（`scripts/onboard_projects.py` が他プロジェクトへ
  配布する際と同じ安全なパターンを踏襲）。

## 実装できなかったこと・人間の操作が必要な項目

1. **Claude Code cloud実行環境からGoogle Media MCP（Cloud Run）へのegress許可**
   — このセッションのagent proxyがHTTP 403（policy denial）で拒否しており、AIエージェント側では
   解決できない。環境管理者またはAnthropicサポートへ、`google-media-mcp-518404402696.us-central1.run.app`
   への到達を許可できないか確認する必要がある。
2. **`GOOGLE_MEDIA_MCP_TOKEN` のClaude Code実行環境への設定** — 設定済みかどうかをこのセッションから
   確認する手段がない。設定手順は `docs/GOOGLE_MEDIA_MCP.md` を参照。
3. **Steel Browser MCPのCloud Runデプロイ** — 課金を伴う人間承認が必要な操作（`AGENTS.md`
   自律実行ルールの例外条件に該当）。`docs/STEEL_BROWSER_MCP.md` の手順に従って人間が実施する。

これらは `AGENTS.md` の「未接続でも全体を停止しない」方針に従い、GitHub Issueまたは
今後のdevlog/引き継ぎで追跡し、全体の作業は停止しない。
