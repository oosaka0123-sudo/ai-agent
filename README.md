# ai-agent

複数のLLM/AIエージェント（Claude Code, Codex, Gemini など）から共同で開発できる、
汎用的なAIエージェント用プロジェクトです。

## このプロジェクトについて

- **目的**: Claude Code / Codex / Gemini など、複数のAIエージェントが同じリポジトリで
  安全かつ効率的に共同開発できるようにすること。
- **現状**: まだ特定の用途（ニュース収集・Web操作・通知・自動処理など）には固定していません。
  必要な機能をこれから追加していける汎用的な構成にしています。

## ディレクトリ構成

```
.
├── .github/          # GitHub Actions（CI）、PR/Issueテンプレート
├── docs/             # 開発ルール・ディレクトリ構成の説明
├── src/              # アプリケーション本体（用途未確定・今後拡張）
├── web/              # GitHub Pagesで公開する静的サイト
├── tests/            # テストコード
├── scripts/          # 開発・運用補助スクリプト
├── config/           # 機密情報を含まない設定ファイル
├── .env.example      # 環境変数サンプル（実際の値は書かない）
├── AGENTS.md         # AIエージェント共通ルール（Codexなどが参照）
├── CLAUDE.md         # Claude Code向け補足
└── GEMINI.md         # Gemini向け補足
```

詳細は [`docs/DIRECTORY_STRUCTURE.md`](docs/DIRECTORY_STRUCTURE.md) を参照してください。

## セットアップ手順（初心者向け）

1. このリポジトリをクローンします。
   ```bash
   git clone <このリポジトリのURL>
   cd ai-agent
   ```
2. 環境変数ファイルを作成します。
   ```bash
   cp .env.example .env
   ```
3. `.env` を開き、必要なAPIキーなどを記入します。
   **`.env` は絶対にGitにコミットしないでください**（`.gitignore` で除外済みです）。
4. 開発ルールを確認します。
   → [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)

まだアプリケーション本体（`src/` の中身）は用意されていません。今後、機能追加とともに
具体的な実行方法をこのセクションに追記していきます。

## 対応しているAIエージェント

このリポジトリには、AIエージェントごとに読み込まれる指示ファイルを用意しています。

| ファイル | 対象 |
|---|---|
| [`AGENTS.md`](AGENTS.md) | 共通ルール（Codexなど汎用的に参照される） |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code向けの補足 |
| [`GEMINI.md`](GEMINI.md) | Gemini向けの補足 |

どのAIエージェントで作業する場合も、まず `AGENTS.md` の内容を確認してから作業してください。

## 公開ページ（GitHub Pages）

`web/` ディレクトリの内容を GitHub Pages でスマホ向けWebページとして公開できる構成にしています。

- ページ本体: `web/index.html`（画像1枚をカード表示するシンプルな構成、スマホ幅で見やすいレスポンシブデザイン）
- デプロイ設定: `.github/workflows/pages.yml`（`main` への push で自動デプロイ）

### 有効化手順（リポジトリ管理者が最初に1回だけ行う作業）

GitHub Pagesの有効化はリポジトリの管理者権限が必要なため、以下はGitHub上での手動設定が必要です。

1. このブランチの内容を Pull Request 経由で `main` にマージする。
2. GitHubリポジトリの `Settings` → `Pages` を開く。
3. 「Build and deployment」の `Source` を **GitHub Actions** に設定する。
4. `main` への push（今回のマージ）をきっかけに `Deploy Pages` ワークフローが自動実行され、
   `https://<ユーザー名>.github.io/ai-agent/` で公開される
   （このリポジトリの場合 `https://oosaka0123-sudo.github.io/ai-agent/`）。

一度設定すれば、以降は `web/` を更新して `main` にマージするだけで自動的に再公開されます。

## セキュリティに関する重要な注意事項

- **APIキー・パスワードなどの秘密情報は絶対にGitHubへコミットしないでください。**
- 秘密情報は `.env` にのみ記載し、`.env.example` にはキー名だけを記載してください。
- `main` ブランチには直接pushせず、必ずPull Requestを経由してください。
- 詳しいルールは [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) を参照してください。

## 今後の拡張予定

このプロジェクトは特定用途に固定していない汎用構成です。今後、以下のような機能を
必要に応じて追加していく想定です。

- ニュース収集機能
- Web操作（ブラウジング・スクレイピングなど）機能
- 通知機能（Slack / Discord など）
- 定期実行・自動処理機能

## ライセンス

未定（プロジェクトの方向性が固まり次第、追記します）。
