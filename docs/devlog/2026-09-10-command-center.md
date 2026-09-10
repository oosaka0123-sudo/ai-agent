# 2026-09-10 AI Development Command Center

## 目的
MY DEVELOPMENT ARCHIVEを、読むための記録サイトから、いま動いているAI開発を判断・統括できる運用司令塔へ進化させる。

## 3者評議
- ChatGPT PM/QA: 情報を増やすより「次に何をするか」「何が正常か」「誰が担当か」を最短で判断できることを優先。
- Claude Code主実装案: JSON駆動の運用スナップショット、次アクション・AI役割・スタック状態を分離し、GitHub Pagesで安全に公開できる静的構成を採用。
- 独立レビュー枠: 状態表示をライブ監視と誤認させないこと、blockedの理由を曖昧にしないこと、390pxで情報密度を保つことを必須条件にした。

## 実装
- `data/command-center.json` を新設。
- `web/command-center.html` を新設。
- `web/assets/js/command-center.js` でJSONを描画。
- 共通ナビに `COMMAND CENTER` を追加。
- Human Gate（secret / billing / destructive operations）を画面上でも明示。

## 品質方針
- 390pxモバイル優先。
- 長い文字列で横スクロールを発生させない。
- `main#main`、キーボードフォーカス、既存共通ナビを維持。
- 本番状態の断定は確認済み事実だけを使う。

## 次工程
PR CI → レビュー → merge → GitHub Pages → live verification の順で完了判定する。
