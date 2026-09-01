# Auto Site Onboarding

新しいWebサイト／PWA／企業サイトを増やしたとき、AI基盤・メディア生成・安全ルールを
毎回手作業で入れ直さないための共通オンボーディングです。

## 目的

新規サイトは **1回登録するだけ** にする。

```text
スマホ
  ↓
Register Site workflow
  ↓
projects/registry.json に登録するPR
  ↓ merge
Auto Site Onboarding
  ↓
対象リポジトリに onboarding PR
  ↓ merge
.ai-agent/project.json が有効
  ↓
共通AI基盤 / Google Vertex AI / 将来のHiggsfield を再利用
```

`max_parallel_projects` は「同時に走らせる作業数」の上限であり、
登録できるサイト総数の上限ではありません。サイトは後から何件でも登録できます。

## 新しいサイトを追加する方法

### スマホから

GitHub Actions の **Register Site** を開き、次だけ入力します。

- slug: `new-company-site`
- name: `新しい会社サイト`
- repository: `owner/new-company-site`
- public_url: 公開URL（まだ無ければ空欄）
- media_provider: 通常は `auto`

workflow が `projects/registry.json` を更新する専用ブランチとPRを作ります。
mainへ直接pushしません。

### CLI / Claude Code / Jules / Codexから

```bash
python3 scripts/register_project.py \
  --slug new-company-site \
  --name "新しい会社サイト" \
  --repository owner/new-company-site \
  --public-url https://example.com/ \
  --media-provider auto
```

## 自動オンボーディング

登録PRをmainへマージすると `.github/workflows/auto-site-onboarding.yml` が動きます。

対象リポジトリには直接mainへ書かず、次の管理ファイルを専用ブランチへ作り、
Pull Requestを開きます。

- `.ai-agent/project.json`
- `.ai-agent/README.md`

`project.json` にはサイト固有情報だけを持たせ、Google/Higgsfieldの認証情報は
各サイトへコピーしません。画像・動画生成の本体は `ai-agent` 側で集中管理します。

## 1回だけ必要なGitHub設定

他リポジトリへPRを作るため、`ai-agent` リポジトリのGitHub Secretに
`CONTROL_PLANE_GITHUB_TOKEN` を登録します。

推奨は fine-grained personal access token または GitHub App token で、
アクセス対象を運用するリポジトリだけに限定し、最低限次を許可します。

- Contents: Read and write
- Pull requests: Read and write
- Metadata: Read

このトークンはコード・`.env.example`・ログへ書きません。

トークンが未設定でもworkflowは壊れず、検証だけ行って「1回設定が必要」と通知します。

## メディア生成の標準

新規サイトのデフォルト:

- provider: `auto`
- Google control-plane project: `rss7-ai-media`
- Google: 主力
- Higgsfield: 接続後のfallback / 別モデル用
- publish policy: `preview-first`
- direct push to main: 禁止

そのため、新しいサイトごとにVertex AIの実装をコピーする必要はありません。
Google/Higgsfieldのモデル変更・ログ・料金制御・ルーティングは司令塔で一元管理します。

## 安全ルール

- target repo の main へ直接pushしない
- onboardingは必ずPR
- 本番自動公開はサイトごとに明示設定するまで有効化しない
- APIキー・Googleサービスアカウント鍵をtarget repoへ配布しない
- FXなど高リスクプロジェクトの安全境界は個別設定を優先する

## 障害時

- repository未接続: registryに残し、接続後の更新で自動対象になる
- token未設定: checkのみ、書き込みなし
- 既に同じmanaged files: `up-to-date` として何もしない
- 内容が変わった: 新しいPRを作る
- target repo APIエラー: 他プロジェクトを続行し、失敗したslugをログに出す
