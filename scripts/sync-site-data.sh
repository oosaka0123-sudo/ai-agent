#!/usr/bin/env bash
# data/ と docs/screenshots/ の中身を、GitHub Pages公開フォルダ(web/)へコピーする。
# ローカルでサイトを確認する前、およびGitHub Actionsのデプロイ時に実行する。
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p web/data web/assets/screenshots

cp -r data/. web/data/

if [ -d docs/screenshots ]; then
  cp -r docs/screenshots/. web/assets/screenshots/
fi

echo "web/data と web/assets/screenshots を最新化しました。"
