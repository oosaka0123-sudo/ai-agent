# Changelog

このファイルには、利用者から見える変更（新機能・修正・破壊的変更）を記録します。
形式はおおむね [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) を参考にしています。
細かい作業ログは [`docs/devlog/`](docs/devlog/) と [`data/devlog.json`](data/devlog.json) を参照してください。

## [Unreleased]

### Added

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
