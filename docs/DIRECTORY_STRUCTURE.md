# ディレクトリ構成

```
.
├── .github/
│   ├── workflows/
│   │   └── ci.yml                  # GitHub Actionsの土台（シークレットスキャン等）
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── pull_request_template.md
├── docs/
│   ├── DEVELOPMENT.md              # 開発ルール
│   ├── DIRECTORY_STRUCTURE.md      # 本ファイル
│   ├── devlog/                     # 開発日記（Markdown、日付ごと）
│   └── screenshots/                # 開発記録用のスクリーンショット保存先
├── data/                           # 開発記録アーカイブサイトのデータ本体
│   ├── projects.json               # プロジェクト一覧データ
│   └── devlog.json                 # 開発記録（タイムライン）データ
├── src/                            # アプリケーション本体（用途未確定・今後拡張）
├── web/                            # GitHub Pagesで公開する静的サイト
│   ├── index.html                  # 開発記録アーカイブ トップページ
│   ├── project.html                # プロジェクト詳細ページ
│   ├── devlog.html                 # 開発記録詳細ページ
│   ├── diagram.html                # リモートAIエージェント構成図ページ
│   └── assets/
├── tests/                          # テストコード
├── scripts/                        # 開発・運用補助スクリプト（sync-site-data.sh 等）
├── config/                         # 機密情報を含まない設定ファイル
├── .env.example                    # 環境変数サンプル
├── .gitignore
├── CHANGELOG.md                    # 利用者から見える変更の記録
├── AGENTS.md                       # AIエージェント共通ルール（開発記録の自動記録ルールを含む）
├── CLAUDE.md                       # Claude Code向け補足
├── GEMINI.md                       # Gemini向け補足
└── README.md
```

## 今後の拡張方針

このプロジェクトは特定の用途に固定していません。今後、例えば以下のような機能を
`src/` 配下にサブディレクトリとして追加していくことを想定しています。

- `src/news/` : ニュース収集機能
- `src/web/` : Webページの閲覧・操作機能
- `src/notify/` : Slack/Discord等への通知機能
- `src/automation/` : 定期実行・自動処理機能
- `src/core/` : 複数機能から共通で使うエージェントのコアロジック

新しい機能を追加する際は、対応するテストを `tests/` に、必要な設定を `config/`
（秘密情報は `.env`）に追加し、`docs/DEVELOPMENT.md` に規約を更新してください。

## web/（GitHub Pages公開サイト）

`web/` は GitHub Pages でそのまま公開される静的サイト用のディレクトリです。
`.github/workflows/pages.yml` が `main` ブランチへの push をトリガーに、
`data/` と `docs/screenshots/` の内容を `web/` へ同期してからデプロイします。
公開方法・有効化手順は [`README.md`](../README.md) の「公開ページ（GitHub Pages）」を参照してください。

## data/・docs/devlog/・docs/screenshots/（開発記録アーカイブのデータ）

「MY DEVELOPMENT ARCHIVE（自分の開発記録）」サイトのデータは、HTMLに直接書き込むのではなく
以下の場所で管理します。

- `data/projects.json` / `data/devlog.json` — サイトが読み込む構造化データ（フィールドの説明は
  [`data/README.md`](../data/README.md)）
- `docs/devlog/YYYY-MM-DD.md` — 人間が読む日単位のMarkdown開発日記
- `docs/screenshots/` — 開発記録に貼る画像の保存先

記録の追加方法・自動記録ルールの詳細は [`AGENTS.md`](../AGENTS.md) の
「開発記録の自動記録ルール」を参照してください。
