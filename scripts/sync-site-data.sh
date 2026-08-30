#!/usr/bin/env bash
# data/ と docs/screenshots/ の中身を、GitHub Pages公開フォルダ(web/)へコピーする。
# ローカルでサイトを確認する前、およびGitHub Actionsのデプロイ時に実行する。
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p web/data web/assets/screenshots web/guides-data

cp -r data/. web/data/
cp -r guides/. web/guides-data/

if [ -d docs/screenshots ]; then
  cp -r docs/screenshots/. web/assets/screenshots/
fi

echo "web/data・web/guides-data・web/assets/screenshots を最新化しました。"
