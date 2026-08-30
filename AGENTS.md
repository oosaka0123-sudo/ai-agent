# AGENTS.md

このファイルは、Claude Code / Codex / Gemini など、このリポジトリで作業する
すべてのAIエージェントが最初に読むべき共通ルールをまとめたものです。
（`CLAUDE.md` や `GEMINI.md` からもこのファイルを参照しています。）

## このプロジェクトについて

複数のLLM/AIエージェント（Claude Code, Codex, Gemini など）が共同で開発できることを
目的とした汎用プロジェクトです。まだ特定の用途には固定されておらず、今後
ニュース収集・Web操作・通知・自動処理などの機能を追加していく予定です。

ディレクトリ構成の詳細は [`docs/DIRECTORY_STRUCTURE.md`](docs/DIRECTORY_STRUCTURE.md)、
開発ルールの詳細は [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) を参照してください。

## 最優先ルール（絶対に守ること）

1. **秘密情報を絶対にコミットしない**
   - APIキー・パスワード・トークンなどは `.env`（gitignore済み）にのみ記述する。
   - `.env.example` には実際の値を書かず、キー名のみを記載する。
   - コミット・PR作成前に、差分に秘密情報が含まれていないか必ず確認する。
2. **`main` ブランチへ直接pushしない**
   - 作業は必ず作業用ブランチ（例: `feature/xxx`, `fix/xxx`）で行い、PR経由で `main` にマージする。
   - `main` は常に動作する状態を保つ。
3. **既存の挙動を壊す変更は、理由をPRに明記する**

## AIエージェントが作業する際の基本フロー

1. `main` を最新化してから作業ブランチを作成する。
2. 変更は小さく、目的が明確な単位でコミットする。
3. コミットメッセージは変更内容が分かるように簡潔に書く。
4. 作業後、`.env` や鍵ファイルなど秘密情報を含むファイルが差分に含まれていないか確認する。
5. PRを作成する場合は `.github/pull_request_template.md` に従って記載する。
6. 他のAIエージェント/人間が並行して作業している可能性があるため、
   push前に最新のリモート状態を取得し、コンフリクトを解消する。

## ディレクトリ構成（概要）

```
.
├── .github/        # GitHub Actions, PR/Issueテンプレート
├── docs/           # ドキュメント（開発ルール、ディレクトリ構成の説明、devlog/screenshots）
├── data/           # 開発記録アーカイブサイトのデータ（projects.json, devlog.json）
├── guides/         # 複数AI比較ガイドのデータ（テーマ別、AIごとに独立したMarkdown）
├── web/            # GitHub Pagesで公開する静的サイト（開発記録アーカイブ、ガイド、構成図など）
├── src/            # アプリケーション本体（用途未確定、今後拡張）
├── tests/          # テストコード
├── scripts/        # 開発・運用補助スクリプト
├── config/         # 機密情報を含まない設定ファイル
├── .env.example    # 環境変数サンプル
├── CHANGELOG.md    # 利用者から見える変更の記録
├── AGENTS.md       # 本ファイル（共通ルール）
├── CLAUDE.md       # Claude Code向け補足
└── GEMINI.md       # Gemini向け補足
```

## 開発記録の自動記録ルール（重要）

このリポジトリには「MY DEVELOPMENT ARCHIVE（自分の開発記録）」という個人用の開発履歴サイトが
`web/index.html` にあります。**開発作業をひとつ完了するたびに、以下を必ず行ってください。**
（ユーザーから明示的に「記録しなくていい」と言われた軽微な作業を除く。）

1. `docs/devlog/YYYY-MM-DD.md` を開く（今日の日付のファイルがなければ
   [`docs/devlog/_template.md`](docs/devlog/_template.md) をもとに新規作成する）。
   同じ日に複数の作業をした場合は見出し（`##`）を分けて追記する。以下を書く。
   - 今日やったこと / 変更したファイル / 追加した機能 / 修正した不具合
   - 使用したAI / 使用技術 / 困ったこと・判断したこと / 学んだこと / 次にやること
2. `data/devlog.json` の配列に、同じ内容を1件構造化データとして追記する
   （フィールドの意味は [`data/README.md`](data/README.md) を参照）。
   - 新しいプロジェクトに関する記録であれば `data/projects.json` にもプロジェクトを追加・更新する。
   - GitHubのコミットやPRを作成した場合は、そのURLを `githubCommits` / `pullRequests` に入れる。
3. 利用者から見える変更（新機能・修正・破壊的変更）であれば `CHANGELOG.md` にも1行追記する。
4. スクリーンショットがあれば `docs/screenshots/` に保存し、`images` / `screenshots` フィールドから
   `assets/screenshots/ファイル名` の形式で参照する（詳細は [`docs/screenshots/README.md`](docs/screenshots/README.md)）。
5. ローカルで確認する場合は `bash scripts/sync-site-data.sh` を実行してから `web/` を開く。

このルールは、後から何年も見返せる開発記録を途切れさせないためのものです。
面倒でも省略せず、必ず実施してください。

## 複数AI比較ガイド（guides/）のルール（重要）

`web/guides/` には、同じテーマについて **Claude Code / Gemini・Jules / Codex が
それぞれ独立して書いた説明を読み比べられるガイド集**があります。
「3つのAIに同じサイトを別々に作らせる」ものでは **ありません**。
サイトのUI・ナビゲーション・データ構造は共通で、テーマごとの「説明文章」だけを
AIごとに分けて `guides/<テーマID>/{claude,gemini,codex}.md` に書きます。

**担当ルール（絶対に守ること）**

- 自分が担当する `.md` ファイルだけを編集する。
  - Claude Code → `claude.md` / Gemini・Jules → `gemini.md` / Codex → `codex.md`
- **他のAIが担当する `.md` ファイルの中身は変更・参考にしない。**
  同じ条件・同じテーマで独立して説明を書くことに意味がある。
- `guides/themes.json`、`guides/<テーマID>/theme.json`、`web/guides/` のHTML/CSS/JSなど
  サイトの共通部分は、どのAIが編集してもよい（新しいテーマの追加、UI改善など）。

詳細は [`guides/README.md`](guides/README.md) を参照してください。

## コーディング規約

言語・フレームワークは現時点で未確定です。機能追加時に採用した言語・フレームワークの
規約（フォーマッタ、リンター等）をこのファイルおよび `docs/DEVELOPMENT.md` に追記してください。

## テスト・CI

`.github/workflows/ci.yml` に土台のみ用意しています。
言語・フレームワークが決まり次第、lint/test/buildのコマンドを追加してください。
