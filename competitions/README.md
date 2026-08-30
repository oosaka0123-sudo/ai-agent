# competitions/ — 3AI競争テスト

`guides/`（複数AI比較ガイド）が「共通のサイト・共通のUIの上で、説明文章だけを
AIごとに独立して書く」仕組みであるのに対し、`competitions/` は
**成果物そのもの（1枚の完結したHTMLページ）を、Claude Code / Gemini・Jules /
OpenAI Codex がそれぞれ完全に独立して作る競争テスト**の記録です。

## ルール

- 各AIは自分の名前を含む専用ブランチで作業する（例:
  `claude-code/competition-01-mobile-ai-dev`）。
- **他のAIのブランチ・成果物・Pull Requestは参照・参考にしない。**
  同じお題に対して、それぞれが独立して調査・設計・実装することに意味がある。
- 成果物は `competitions/<回番号>-<お題の短縮名>/<ai-name>.html` に置く
  （例: `competitions/01-mobile-ai-dev/claude-code.html`）。
- `main` へは直接pushせず、作業ブランチからPull Requestを作成する。
  **Pull Requestを作成した時点で作業は完了とし、`main` へはマージしない**
  （マージ判断はユーザーが行う）。
- 完了までの流れ（実装 → テスト → 自己レビュー → 問題修正 → 再テスト →
  開発ログ記録 → コミット → push → PR作成）は [`AGENTS.md`](../AGENTS.md) の
  「自律実行ルール」「自己評価・品質保証」に従う。

## 第1回: スマホだけでAI開発はどこまでできる？

- お題ディレクトリ: `01-mobile-ai-dev/`
- テーマ: Claude Code・Gemini/Jules・OpenAI Codexを比較しながら、
  スマートフォンだけで「調査 → 設計 → コーディング → テスト → GitHub保存 → 公開」
  までどこまで実践できるかをまとめた、初心者向けの1枚完結ガイド。
- 成果物: `claude-code.html`（Claude Code版。他AI版は各AIが自分のブランチ・
  Pull Requestで独立して追加する）。
