# Changelog

このファイルには、利用者から見える変更（新機能・修正・破壊的変更）を記録します。
形式はおおむね [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) を参考にしています。
細かい作業ログは [`docs/devlog/`](docs/devlog/) と [`data/devlog.json`](data/devlog.json) を参照してください。

## [Unreleased]

### Added

- 「複数AI比較ガイド」機能の最初のテーマ「スマホだけでホームページを作る」について、Gemini/Jules担当の説明本文（`guides/smartphone-website/gemini.md`）を追加。

### Changed

- リポジトリの目的を「Claude Code・Gemini/Jules・OpenAI Codexの3AIがGitHubを
  共通記憶として並行作業できるAIエージェント開発基盤」として明確化し、
  `README.md`・`AGENTS.md`・`PROJECT_SPEC.md` の記述を統一。
  MY DEVELOPMENT ARCHIVEと複数AI比較ガイドは、この基盤の動作確認用
  サンプルプロジェクトである旨を明記した。
- `README.md` に、会話履歴のない新規AIセッション向けのオンボーディング手順
  （読む順番）を追加。
- `CODEX.md` を新規追加し、`CLAUDE.md` / `GEMINI.md` と対称の構成にした。
  `GEMINI.md` は「Gemini / Jules」向けの内容に更新。

### Added

- `AGENTS.md` に「自律実行ルール」「自己評価・品質保証」を追加し、
  `PROJECT_SPEC.md`（機能仕様）と `docs/devlog/self-eval/`（AIごとの自己評価ログ）を新設。
- 「複数AI比較ガイド」機能を追加。同じテーマについて Claude Code・Gemini/Jules・Codex が
  独立して書いた説明を読み比べられる `web/guides/`（一覧・テーマ・説明表示ページ）を追加し、
  データを `guides/themes.json` / `guides/<テーマID>/theme.json` / `guides/<テーマID>/{claude,gemini,codex}.md`
  で管理する構成にした。最初のテーマ「スマホだけでホームページを作る」を用意（本文は未執筆のプレースホルダー）。
  `scripts/sync-site-data.sh` と `pages.yml` を拡張し `guides/` も `web/` へ同期するようにした。
- 個人用の開発記録アーカイブサイト「MY DEVELOPMENT ARCHIVE（自分の開発記録）」を追加。
  トップページ（検索・AI/技術タグ絞り込み・タイムライン・プロジェクト一覧）、
  プロジェクト詳細ページ、開発記録詳細ページを `web/` に構築。
  データは `data/projects.json` / `data/devlog.json` で管理し、
  `docs/devlog/` に日単位のMarkdown開発日記を残す運用にした。
- `scripts/sync-site-data.sh` を追加。`data/` と `docs/screenshots/` を
  GitHub Pages公開フォルダ `web/` へ同期する。
- 「スマホで作るリモートAIエージェント最強構成」の構成図ページ（`web/diagram.html`）を追加し、
  GitHub Pagesで自動公開する `.github/workflows/pages.yml` を追加。
- リポジトリ初期構成（README、`.gitignore`、`.env.example`、`AGENTS.md`/`CLAUDE.md`/`GEMINI.md`、
  CI（シークレットスキャン）、開発ルールドキュメント）を追加。

### Fixed

- デスクトップ幅でカード・グリッドの要素数が少ないときに右側へ余白が偏っていた
  問題を、`grid-template-columns` を `auto-fill` から `auto-fit` に変更して解消。
- `devlog.html` で一部フィールドを冗長に二重評価していた処理を整理。
- トップページの検索欄に `aria-label` を追加し、アクセシビリティを改善。
