# Agent Handoff テンプレート

<!--
使い方:
1. このファイルをコピーしてリポジトリ直下に `HANDOFF.md` を作成する
   （複数AIが同時に引き継ぎを作る場合は
   `docs/handoffs/<YYYY-MM-DD-HHMM>_<agent>_HANDOFF.md` のように衝突しない名前にし、
   `HANDOFF.md` から最新ファイルを案内する）。
2. 過去チャットの記憶だけで書かず、可能な範囲でGitHubの現在状態
   （current branch, Issue, PR, Actions, commit）を確認してから書く。
3. 確認済みの事実は OBSERVED、推測・未確認は HYPOTHESIS と明記する。
4. パスワード・APIキー・Token・Cookie・秘密鍵・認証情報・個人情報は書かない。
5. `oosaka0123-sudo/ai-master` の `AGENTS.md`
   （Context Handoff Protocol — 40% Rule）と対になるProjectローカルの実体。
   Masterへ進捗をコピーしない。
-->

# Agent Handoff

Project: ai-agent
Repository: oosaka0123-sudo/ai-agent

## Goal

- ユーザーが最終的に実現したいこと:
- 今回の作業範囲:
- 完了条件:

## Current Status

- 現在のdefault branch:
- 現在の作業branch:
- 関連Issue / PR（実確認できたものだけ）:

## Completed（OBSERVED）

-

## Remaining

-

## Files Changed

- 変更したファイル:
- 変更理由:
- 重要な実装判断:

## Tests

- 実行したテスト:
- 成功 / 失敗:
- 未実施の検証:
- CI / Actionsの状態:

## Problems

- 現在のブロッカー:
- 壊れやすい箇所・未確認事項（HYPOTHESISは明記する）:

## User-fixed decisions（ユーザー確定事項・禁止事項）

-

## Next Agent

- 次の担当（Claude / Claude Cowork / Claude Code / Gemini・Jules / Codex / ChatGPT等、
  未確定なら「未定・次セッションで判断」と書く）:

## Next Action

- 次に最初に読むファイル:
- 次に最初に確認するGitHub実態:
- 次の具体的な1〜5ステップ:

## 再開用最短メッセージ

<!-- 新しいチャット・別AIにそのまま渡せる短い再開指示 -->

「`README.md` → `AGENTS.md` → この `HANDOFF.md` の順に読み、GitHubの現在状態
（Issue / PR / Actions / current code）を確認してから、未完了の次ステップから再開する。」
