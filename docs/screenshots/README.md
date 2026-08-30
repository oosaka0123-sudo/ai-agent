# docs/screenshots/ — 開発記録用スクリーンショット

開発記録（`data/devlog.json`、`data/projects.json`）に貼り付ける画像はここに保存してください。

## 使い方

1. 画像ファイルをこのディレクトリに置く。
   - 例: `docs/screenshots/2026-08-30-ai-agent-dashboard.png`
   - ファイル名は「日付-内容がわかる名前」にすると後から探しやすい。
2. `data/devlog.json` の該当する開発記録の `images` 配列、または
   `data/projects.json` の該当プロジェクトの `screenshots` 配列に、
   `assets/screenshots/ファイル名` の形式でパスを追記する
   （`docs/screenshots/` ではなく `assets/screenshots/` と書く点に注意。
   公開時に `scripts/sync-site-data.sh` がこのディレクトリの中身を
   `web/assets/screenshots/` へコピーするため）。
3. `bash scripts/sync-site-data.sh` を実行してからサイトを開くと、
   ローカルでも画像が表示されることを確認できます。

## 注意事項

- 秘密情報（APIキー・個人情報・非公開の管理画面など）が写り込んだ画像は
  絶対にここへ置かないでください（このリポジトリはGitHub Pagesで公開されます）。
- 画像サイズが大きすぎるとスマホでの表示が重くなるため、可能であれば
  1枚あたり数百KB程度に圧縮してから追加することを推奨します。
