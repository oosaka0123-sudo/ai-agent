# GEMINI.md

Gemini CLI / Jules（および他のGemini系エージェント）向けの補足ファイルです。
このリポジトリでは "Gemini・Jules" を1つの担当単位として扱っています
（[`guides/`](guides/README.md) の担当ファイルも `gemini.md` で共通）。
共通ルールは [`AGENTS.md`](AGENTS.md) にまとめてあるので、作業を始める前に必ずそちらを読んでください。

## Gemini / Jules 固有の注意事項

- 秘密情報（APIキー等）を出力・ログ・コミットメッセージに含めない。
- 作業用ブランチで開発し、`main` へ直接pushしない（詳細は `AGENTS.md` 参照）。
- `AGENTS.md` の「自律実行ルール」に従い、明確な仕様がある作業は途中で
  確認を挟まず最後まで完了させる。停止してよい例外は `AGENTS.md` を参照する。
- 不明点や仕様が確定していない部分は、推測で実装を進めず、
  `docs/DEVELOPMENT.md` の方針に沿っているか確認する。
- GitHub Issue経由の正式発注フローについては [`docs/JULES_ISSUE_DISPATCH.md`](docs/JULES_ISSUE_DISPATCH.md) を参照。
- `guides/smartphone-website/gemini.md` など、Gemini・Julesが担当するファイルにのみ
  執筆する。他のAI（Claude Code, Codex）が担当するファイルは変更しない
  （詳細は `AGENTS.md` の「複数AI比較ガイド（guides/）のルール」を参照）。
