# CLAUDE.md

Claude Code 向けの補足ファイルです。共通ルールは [`AGENTS.md`](AGENTS.md) に
まとめてあるので、作業を始める前に必ずそちらを読んでください。

## Claude Code 固有の注意事項

- 破壊的な操作（`git push --force`、`git reset --hard`、ファイルの一括削除など）を
  行う前は、必ずユーザーに確認する（`AGENTS.md` の「自律実行ルール」の例外に該当する）。
- それ以外の、明確な仕様がある作業は `AGENTS.md` の「自律実行ルール」に従い、
  途中で確認を挟まず最後まで完了させる。
- 秘密情報（`.env` の中身など）を出力・ログ・コミットメッセージ・PR本文に含めない。
- 作業用ブランチで開発し、`main` へ直接pushしない（詳細は `AGENTS.md` 参照）。
- `guides/smartphone-website/claude.md` など、Claude Codeが担当するファイルにのみ
  執筆する。他のAI（Gemini・Jules, Codex）が担当するファイルは変更しない
  （詳細は `AGENTS.md` の「複数AI比較ガイド（guides/）のルール」を参照）。
- リポジトリ固有の開発ルールは [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) を参照する。
