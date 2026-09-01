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

## generate_media.py

Google Vertex AI（公式 `google-genai` SDK）を使って画像・動画を生成する共通CLIです。
実装は `src/media_gen/` にあり、このスクリプトはそのエントリーポイントです。
詳しい使い方・事前準備・接続テスト方法は [`../README.md`](../README.md) の
「メディア生成（Vertex AI連携）」を参照してください。

```bash
pip install -r ../requirements.txt  # リポジトリルートで実行する場合は requirements.txt
python3 scripts/generate_media.py --provider google --type image --prompt "夕焼けの東京タワー"
python3 scripts/generate_media.py --provider google --type video --prompt "海辺を歩く猫" --aspect-ratio 9:16
```
