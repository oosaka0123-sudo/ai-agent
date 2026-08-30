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
│   └── DIRECTORY_STRUCTURE.md      # 本ファイル
├── src/                            # アプリケーション本体（用途未確定・今後拡張）
├── web/                            # GitHub Pagesで公開する静的サイト
│   ├── index.html
│   └── assets/
├── tests/                          # テストコード
├── scripts/                        # 開発・運用補助スクリプト
├── config/                         # 機密情報を含まない設定ファイル
├── .env.example                    # 環境変数サンプル
├── .gitignore
├── AGENTS.md                       # AIエージェント共通ルール
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
`.github/workflows/pages.yml` が `main` ブランチへの push をトリガーに `web/` の内容を
ビルドせずそのままデプロイします。公開方法・有効化手順は [`README.md`](../README.md) の
「公開ページ（GitHub Pages）」を参照してください。
