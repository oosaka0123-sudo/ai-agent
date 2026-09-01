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

## register_project.py

新しいサイト／プロジェクトを `projects/registry.json` へ追加します。
標準では `auto_onboard=true`、media providerは `auto`、共有Google projectは `rss7-ai-media` です。

```bash
python3 scripts/register_project.py \
  --slug new-site \
  --name "New Site" \
  --repository owner/new-site \
  --public-url https://example.com/
```

スマホからは `.github/workflows/register-site.yml` の **Register Site** でも同じ登録PRを作れます。

## onboard_projects.py

registryに登録済みで `repository` が接続されているプロジェクトへ、
`.ai-agent/project.json` / `.ai-agent/README.md` を専用ブランチ + PRで配布します。
target repoのmainへ直接pushしません。

検証だけ:

```bash
python3 scripts/onboard_projects.py --check
```

実際にPRを作成:

```bash
CONTROL_PLANE_GITHUB_TOKEN=... python3 scripts/onboard_projects.py --apply
```

cross-repo tokenはGitHub Secretで管理し、コードへ保存しません。
詳細は `docs/AUTO_SITE_ONBOARDING.md` を参照してください。
