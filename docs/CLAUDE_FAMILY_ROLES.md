# Claude製品ファミリーの役割分担とMCP分類

更新日: 2026-09-06

このドキュメントは、**Claude / Claude Cowork / Claude Code** という同じベンダーの
3製品を、このリポジトリの基盤（`AGENTS.md` の自律実行ルール・自己評価ルール・
ブランチ運用）の上でどう役割分担させるか、および接続するMCPサーバーをどう分類・
配線するかをまとめたものです。

`docs/GPT_GITHUB_CONTROL.md`（ChatGPT/GPT向け）、
`docs/MULTI_PROJECT_ORCHESTRATION.md`（複数プロジェクト運用）と対になる、
Claude製品ファミリー向けの補足です。Claude Code固有の詳細注意点は
[`CLAUDE.md`](../CLAUDE.md) を参照してください。

## この文書の位置づけ（重要）

`oosaka0123-sudo/ai-master` の `AGENTS.md`（ADR-012）は、
「Claude Code / Jules / Codex / Copilot / Gemini等の製品名と役割はMasterの
不変ルールとして固定しない。実際の担当はCapability-based Routing（`CONNECT.md`と
対象ProjectのGitHub実態）で決める」という方針を採用しています。

このドキュメントはその方針と矛盾しません。以下は**このリポジトリ（ai-agent）で
作業する場合のDEFAULTの役割分担（推奨パターン）**であり、Masterの不変ルールでは
ありません。実際にどの製品がどこまで接続・実行できるかは、セッションごとに
実アクセスで確認してください（未接続でも他の担当が代替できる範囲は作業を止めない、
という `AGENTS.md` の「自律実行ルール」の考え方に従います）。

## 役割分担

| 製品 | このリポジトリでの役割 | 担当しないこと |
|---|---|---|
| **Claude**（chat） | 要件整理・アーキテクチャ検討・設計相談・仕様決定支援・コードレビュー・調査・問題分析。`MULTI_PROJECT_ORCHESTRATION.md` でChatGPTが担っている「全体設計・優先順位付け」と同じ設計・判断・PM層をClaude製品側からも担える。 | 大量のコード直接編集、Repository操作、Branch/PR作成。 |
| **Claude Cowork** | 複数サービス（GitHub・Google・MCP・ローカルファイル・ドキュメント）をまたぐ横断作業のオーケストレーション、調査、プロジェクト管理、Claude Codeへの実装指示作成、複数AIの作業結果の集約。 | コードの大量直接編集は自分で無理に処理せず、Claude Codeへ委譲する。Repository本体へのCommit/PRは基本的に行わない（`main`直接pushは`AGENTS.md`により全AI共通で禁止）。 |
| **Claude Code** | GitHub Repository操作（Branch/Commit/PR）、コード実装・リファクタリング、MCP設定（`.mcp.json`等）、環境変数設定、API接続コード、GitHub Actions/CI/CD、テスト、デバッグ。既存の「3AI」枠（`CLAUDE.md`/`GEMINI.md`/`CODEX.md`）における実装担当そのもの。 | — |

この役割分担は、既存の `MULTI_PROJECT_ORCHESTRATION.md` の
「ChatGPTは全体設計・作業分割・優先順位・GitHub操作の統括」「Claude Code / Codex /
Julesは実装担当」という構造をClaude製品ファミリー内に写像したものです。
ChatGPTとClaude/Claude Coworkは同じ設計・オーケストレーション層として併存でき、
どちらを使うかはユーザーの選択・接続状況次第です。

## 重複作業の防止

`AGENTS.md` の自律実行ルールおよび `ai-master/AGENTS.md` ADR-012
「1 Task = 1 Active Owner」に従い、Claude CoworkがClaude Codeへ実装を委譲する前に、
対象範囲で既にOpenな Issue / Branch / PR がないか（他AI・人間による作業を含む）を
確認してから着手します。同一スコープの重複実装を避け、他AIの担当ファイル
（`guides/` の担当分など）を横取りしません。

## MCP分類（Development / Knowledge-Work / Media）

MCPサーバーは場当たり的に追加せず、用途で3層に分類し、どのClaude製品が
主担当として接続するかを決めます。

| 分類 | 用途 | 主担当 | このリポジトリの実例 |
|---|---|---|---|
| **Development MCP** | 開発・テスト・Repository操作 | Claude Code | GitHub MCP、filesystem/repo操作系MCP |
| **Knowledge / Work MCP** | 調査・資料・業務・自動化・プロジェクト運営、複数アプリ横断 | Claude Cowork | Google Drive MCP、（将来）Gmail/Calendar/Docs/Sheets MCP、Steel Cloud Browser（`mcp_server/steel_browser/`、[`docs/STEEL_BROWSER_MCP.md`](STEEL_BROWSER_MCP.md)） |
| **Media MCP** | 画像・動画・Webコンテンツ制作 | Claude Cowork がオーケストレーション、実装はClaude Codeが `mcp_server/` へAPI実装 | Google Media MCP（`mcp_server/`、[`docs/GOOGLE_MEDIA_MCP.md`](GOOGLE_MEDIA_MCP.md)） |

判断基準（MCPをどこへ接続するか）:

1. コード変更やRepository操作が中心 → Claude Codeへ接続（Development MCP）
2. 複数アプリ・ドキュメント・ブラウザ・業務ツールを横断する → Claude Coworkへ接続
   （Knowledge / Work MCP）
3. 本番Webサイト・アプリから継続的に呼ぶ機能 → MCPではなくAPI直接接続にする
4. 複数エージェントから共通に必要なサービス → 共有Remote HTTP MCP化する
   （既存例: Google Media MCP、Steel Browser MCP。いずれも `mcp_server/` が
   Inbound Bearer Auth とアップストリーム認証情報を分離するパターンを採用しており、
   新しい共有MCPを追加する場合もこの最小権限パターンを踏襲する）

## MCPとAPIを混同しない（既存の実例）

このリポジトリには、同じ機能を「一時的なAI作業向けMCP」と「継続的な本番利用向けAPI」に
分けて実装した実例が既にあります。

- `scripts/generate_media.py`（CLI/直接呼び出し）: 開発者・AIエージェントが手動で
  1回だけ画像・動画生成を試す用途。
- `mcp_server/`（Remote HTTP MCP）: 全Claude Codeプロジェクトから共通ツールとして
  常時呼べるようにした配布層。同じ `src/media_gen/` バックエンドを再利用し、
  実装を重複させていない。

新しい機能を追加する場合も、「AIが作業中に一時的に操作する」用途はMCP、
「Webサイト/アプリから毎日自動で呼ぶ」用途はAPI（またはAPIをラップしたスクリプト）
という区別を踏襲してください。

## Secret管理・最小権限

このリポジトリの秘密情報管理方針（`.env` のみに実値を書く、`.env.example` は
キー名のみ、`main`直接push禁止など）は製品を問わず共通です。詳細は
[`AGENTS.md`](../AGENTS.md) の「最優先ルール」と [`docs/DEVELOPMENT.md`](DEVELOPMENT.md)
を参照してください。

MCPサーバー側の最小権限パターン（Inbound認証とアップストリーム認証情報の分離、
Read専用処理へWrite権限を渡さない等）は、既存の
[`docs/GOOGLE_MEDIA_MCP.md`](GOOGLE_MEDIA_MCP.md) /
[`docs/STEEL_BROWSER_MCP.md`](STEEL_BROWSER_MCP.md) を新規MCP追加時のテンプレートとして
再利用してください。

## Agent間の引き継ぎ

Claude / Claude Cowork / Claude Code間、および他AI（Gemini・Jules, Codex, ChatGPT）
との引き継ぎは、`AGENTS.md` の「チャット保存 / Knowledge routing」節と
`ai-master/AGENTS.md` の Context Handoff Protocol（40% Rule）に従います。
このリポジトリで実際に引き継ぎファイルを作る場合の標準テンプレートは
[`docs/HANDOFF_TEMPLATE.md`](HANDOFF_TEMPLATE.md) を使い、コピーして
`HANDOFF.md` を作成してください（形式だけの空ファイルを先回りで作らないため、
テンプレート自体は雛形として `docs/` に置き、実際の引き継ぎが必要になった時点で
リポジトリ直下へ実体を作ります）。

## 接続できない場合

Claude / Claude Cowork / Claude Code のいずれか、または特定のMCP/Connectorが
未接続でも、`AGENTS.md` の自律実行ルールに従い、利用可能な範囲で作業を進めます。
未接続部分はGitHub Issue・TODO・`docs/HANDOFF_TEMPLATE.md` を使った引き継ぎとして残し、
後から接続したAgentが続行できる状態にします。
