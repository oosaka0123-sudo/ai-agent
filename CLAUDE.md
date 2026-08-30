# CLAUDE.md

Claude Code 向けの補足ファイルです。共通ルールは [`AGENTS.md`](AGENTS.md) に
まとめてあるので、作業を始める前に必ずそちらを読んでください。

## Claude Code 固有の注意事項

- 破壊的な操作（`git push --force`、`git reset --hard`、ファイルの一括削除など）を
  行う前は、必ずユーザーに確認する。
- 秘密情報（`.env` の中身など）を出力・ログ・コミットメッセージ・PR本文に含めない。
- 作業用ブランチで開発し、`main` へ直接pushしない（詳細は `AGENTS.md` 参照）。
- リポジトリ固有の開発ルールは [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) を参照する。
