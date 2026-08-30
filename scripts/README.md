# scripts/

開発・運用を補助するスクリプト（セットアップスクリプト、バッチ処理、デプロイ補助など）を配置するディレクトリです。

再利用可能な処理は `src/` に、単発の運用・開発補助スクリプトはこちらに置くことを想定しています。

## sync-site-data.sh

`data/` と `docs/screenshots/` の中身を、GitHub Pages公開フォルダ `web/` へコピーするスクリプトです。
開発記録アーカイブサイト（`web/index.html`）をローカルで確認する前に実行してください。

```bash
bash scripts/sync-site-data.sh
python3 -m http.server 8000 --directory web
# ブラウザで http://localhost:8000/ を開く
```

`main` ブランチへの push時は、GitHub Actions（`.github/workflows/pages.yml`）が同じスクリプトを
自動実行してから公開するため、手動でこの内容を `web/` にコピーしてコミットする必要はありません。
