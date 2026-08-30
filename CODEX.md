# CODEX.md

OpenAI Codex（Codex CLI / Codex系エージェント）向けの補足ファイルです。
共通ルールは [`AGENTS.md`](AGENTS.md) にまとめてあるので、作業を始める前に必ずそちらを読んでください
（Codex CLIは標準で `AGENTS.md` を参照する設計になっているため、このファイルはその上に
Codex固有の注意点だけを補足するものです）。

## Codex 固有の注意事項

- 秘密情報（APIキー等）を出力・ログ・コミットメッセージ・PR本文に含めない。
- 作業用ブランチで開発し、`main` へ直接pushしない（詳細は `AGENTS.md` 参照）。
- `AGENTS.md` の「自律実行ルール」に従い、明確な仕様がある作業は途中で
  確認を挟まず最後まで完了させる。停止してよい例外は `AGENTS.md` を参照する。
- `guides/smartphone-website/codex.md` など、Codexが担当するファイルにのみ執筆する。
  他のAI（Claude Code, Gemini・Jules）が担当するファイルは変更しない
  （詳細は `AGENTS.md` の「複数AI比較ガイド（guides/）のルール」を参照）。
- リポジトリ固有の開発ルールは [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) を参照する。
