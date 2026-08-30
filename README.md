# ai-agent

**Claude Code / Gemini・Jules / OpenAI Codex** の3AIが、GitHubを共通記憶として
並行作業できるAIエージェント開発基盤です。

## このプロジェクトについて

- **本当の目的**: Web / PWA / API連携 / 自動化 / 調査 / 通知 / アプリなど、
  さまざまなものを複数のAIエージェントがチームとして作れる汎用基盤を作ること。
  会話履歴を共有できない複数のAI（Claude Code, Gemini・Jules, Codex など）が、
  **GitHubリポジトリそのものを共通の記憶**として読み書きすることで、
  途切れずに共同開発を続けられるようにする。
- **Webサイト制作そのものが目的ではない**: リポジトリ内には
  「MY DEVELOPMENT ARCHIVE」や「複数AI比較ガイド」といったWebサイトが
  すでに存在するが、これらは **この基盤が実際に機能するかを確かめるための
  サンプル（例示）プロジェクト**であり、目的そのものではない。
  今後は用途を問わず、あらゆる種類の成果物（PWA、API、自動化スクリプト、
  調査・通知の仕組みなど）をこの基盤の上に追加していく。
- **現状**: 特定の用途に固定していない汎用的な構成。安全なブランチ運用・
  秘密情報管理・自律実行ルール・自己評価ルールなど、AIチームが安心して
  並行作業できるための土台を優先して整備している。

## 初めてこのリポジトリを開くAIエージェントへ（オンボーディング）

会話履歴が残っていない状態で作業を始める場合は、以下の順番で読んでください。
これだけ読めば、これまでの経緯を知らなくてもプロジェクトの目的・ルール・
現状を把握できるように書かれています。

1. **`README.md`（このファイル）** — プロジェクトの目的・全体構成・各種手順
2. **[`AGENTS.md`](AGENTS.md)** — 3AI共通のルール（最優先ルール・自律実行ルール・
   自己評価ルール・自動記録ルールなど）。作業前に必ず読む。
3. **[`PROJECT_SPEC.md`](PROJECT_SPEC.md)** — 実装済み・実装予定の機能仕様。
   作業前に現状を把握し、作業後にここと突き合わせて自己レビューする。
4. **自分のAI向け補足ファイル** — [`CLAUDE.md`](CLAUDE.md) / [`GEMINI.md`](GEMINI.md) /
   [`CODEX.md`](CODEX.md) のうち、自分に該当するもの。
5. **[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)** — ブランチ運用・コミット・PRなど詳細ルール
6. **[`docs/devlog/`](docs/devlog/)** と **[`docs/devlog/self-eval/`](docs/devlog/self-eval/)** —
   これまでの作業履歴と、AIごとの自己評価の記録（自分の担当分を確認・追記する）

## ディレクトリ構成

```
.
├── .github/          # GitHub Actions（CI）、PR/Issueテンプレート
├── docs/             # 開発ルール・ディレクトリ構成の説明・開発日記・スクリーンショット
├── data/             # 開発記録アーカイブサイトのデータ（projects.json / devlog.json）
├── guides/           # 複数AI比較ガイドのデータ（テーマ別、AIごとに独立したMarkdown）
├── src/              # アプリケーション本体（用途未確定・今後拡張）
├── web/              # GitHub Pagesで公開する静的サイト（開発記録アーカイブ、ガイド、構成図）
├── tests/            # テストコード
├── scripts/          # 開発・運用補助スクリプト
├── config/           # 機密情報を含まない設定ファイル
├── .env.example      # 環境変数サンプル（実際の値は書かない）
├── CHANGELOG.md      # 利用者から見える変更の記録
├── AGENTS.md         # AIエージェント共通ルール（Codexなどが参照）
├── CLAUDE.md         # Claude Code向け補足
├── GEMINI.md         # Gemini/Jules向け補足
└── CODEX.md          # OpenAI Codex向け補足
```

詳細は [`docs/DIRECTORY_STRUCTURE.md`](docs/DIRECTORY_STRUCTURE.md) を参照してください。

## セットアップ手順（初心者向け）

1. このリポジトリをクローンします。
   ```bash
   git clone <このリポジトリのURL>
   cd ai-agent
   ```
2. 環境変数ファイルを作成します。
   ```bash
   cp .env.example .env
   ```
3. `.env` を開き、必要なAPIキーなどを記入します。
   **`.env` は絶対にGitにコミットしないでください**（`.gitignore` で除外済みです）。
4. 開発ルールを確認します。
   → [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)

まだアプリケーション本体（`src/` の中身）は用意されていません。今後、機能追加とともに
具体的な実行方法をこのセクションに追記していきます。

## 対応しているAIエージェント

このリポジトリには、AIエージェントごとに読み込まれる指示ファイルを用意しています。

| ファイル | 対象 |
|---|---|
| [`AGENTS.md`](AGENTS.md) | 3AI共通ルール（Codex CLIなどが標準で参照するファイル名でもある） |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code向けの補足 |
| [`GEMINI.md`](GEMINI.md) | Gemini / Jules向けの補足 |
| [`CODEX.md`](CODEX.md) | OpenAI Codex向けの補足 |

どのAIエージェントで作業する場合も、まず `AGENTS.md` の内容を確認してから作業してください。

## サンプルプロジェクト（基盤の動作確認用）

この基盤が実際に機能するかを確認するために、これまで以下の2つのサンプルを
作成しました。**いずれもこの基盤の主目的ではなく、動作確認・使い方の実例です。**
今後はWebサイトに限らず、PWA・API連携・自動化・調査・通知などのプロジェクトも
同じ基盤（ブランチ運用・自律実行ルール・自己評価ルール・開発記録ルール）の上に
追加していきます。

### MY DEVELOPMENT ARCHIVE（自分の開発記録）

このリポジトリには、自分がこれまで行ってきた開発（Webサイト・アプリ・AIエージェント・PWA・
実験など）を、後からスマホで簡単に振り返るための個人用アーカイブサイトが入っています。

- サイト名: **MY DEVELOPMENT ARCHIVE**（日本語表示名: 「自分の開発記録」）
- 中身: `web/index.html`（トップページ）、`web/project.html`（プロジェクト詳細）、
  `web/devlog.html`（開発記録詳細）
- データ: `data/projects.json`（プロジェクト一覧）、`data/devlog.json`（開発記録タイムライン）
- 日記: `docs/devlog/YYYY-MM-DD.md`（人間が読む日単位のMarkdown日記）
- 画像: `docs/screenshots/`（開発記録に貼るスクリーンショット）

トップページでは、開発件数・最近の開発・プロジェクト一覧・開発タイムライン・使用したAI一覧・
使用技術一覧を確認でき、検索ボックスやAI/技術タグのタップでタイムラインとプロジェクト一覧を
絞り込めます。各カードから、目的・変更内容・使ったAI/技術・困ったこと・学んだこと・画像・
GitHubコミットなどをまとめた詳細ページを開けます。

#### 開発記録の追加方法

新しい開発記録を追加するときは、HTMLを直接編集するのではなく、以下のデータファイルを編集します。

1. `docs/devlog/YYYY-MM-DD.md` を作成・追記する（[`docs/devlog/_template.md`](docs/devlog/_template.md) をコピーして使う）。
2. `data/devlog.json` の配列に、同じ内容を1件JSONとして追記する
   （フィールドの意味は [`data/README.md`](data/README.md) を参照）。
3. 新しいプロジェクトなら `data/projects.json` にも1件追加する。
4. スクリーンショットがあれば `docs/screenshots/` に置き、
   `assets/screenshots/ファイル名` の形式でパスを記述する。

**Claude Codeなど、AIエージェントに開発作業を依頼している場合は、
作業完了後にこの手順を自動で行うルールを [`AGENTS.md`](AGENTS.md) の
「開発記録の自動記録ルール」に定めています。** 何年も記録を続けられるよう、
このルールは省略せず徹底してください。

#### 運用方法（ローカルで確認する）

`data/` や `docs/screenshots/` を編集した内容は、まず `web/` へ同期してから確認します。

```bash
bash scripts/sync-site-data.sh
python3 -m http.server 8000 --directory web
# ブラウザで http://localhost:8000/ を開く
```

（`fetch` でJSONを読み込む構成のため、`web/index.html` をブラウザで直接開いても
データは表示されません。必ずローカルサーバー経由で開いてください。）

#### 公開方法（GitHub Pages）

- ページ本体: `web/` 以下（トップページ・詳細ページ・構成図ページ `web/diagram.html`）
- デプロイ設定: `.github/workflows/pages.yml`（`main` への push で、
  `data/`・`guides/`・`docs/screenshots/` を `web/` へ同期してから自動デプロイ）

##### 有効化手順（リポジトリ管理者が最初に1回だけ行う作業）

GitHub Pagesの有効化はリポジトリの管理者権限が必要なため、以下はGitHub上での手動設定が必要です。

1. このブランチの内容を Pull Request 経由で `main` にマージする。
2. GitHubリポジトリの `Settings` → `Pages` を開く。
3. 「Build and deployment」の `Source` を **GitHub Actions** に設定する。
4. `main` への push（今回のマージ）をきっかけに `Deploy Pages` ワークフローが自動実行され、
   `https://<ユーザー名>.github.io/ai-agent/` で公開される
   （このリポジトリの場合 `https://oosaka0123-sudo.github.io/ai-agent/`）。

一度設定すれば、以降は `data/devlog.json` などを更新して `main` にマージするだけで
自動的に再公開されます。

### ガイド（複数AI比較）

`web/guides/` には、同じテーマについて **Claude Code・Gemini/Jules・Codexがそれぞれ
独立して書いた説明を読み比べられるガイド集**があります。「3つのAIに同じサイトを
別々に作らせる」ものではなく、**サイトのUI・データ構造は共通**で、テーマごとの
「説明文章」だけをAIごとに分けて管理します。

- 一覧: `web/guides/index.html`（テーマ一覧） → `web/guides/theme.html`（3AI選択）
  → `web/guides/view.html`（各AIの説明を表示）
- データ: `guides/themes.json`（テーマ一覧）、`guides/<テーマID>/theme.json`（テーマ情報）、
  `guides/<テーマID>/{claude,gemini,codex}.md`（各AIの説明本文）

最初のテーマは「スマホだけでホームページを作る」です。Gemini/Jules版・Codex版は
本文を公開済みで、Claude Code版はまだ見出し構成のみのプレースホルダーです。

**担当ルール**: 各AIは自分の担当ファイル（`claude.md` / `gemini.md` / `codex.md`）
だけを編集し、他AIのファイルは変更しません。共通UI（HTML/CSS/JS、`themes.json` など）
はどのAIが編集してもかまいません。詳細は [`guides/README.md`](guides/README.md) と
[`AGENTS.md`](AGENTS.md) の「複数AI比較ガイド（guides/）のルール」を参照してください。

## セキュリティに関する重要な注意事項

- **APIキー・パスワードなどの秘密情報は絶対にGitHubへコミットしないでください。**
- 秘密情報は `.env` にのみ記載し、`.env.example` にはキー名だけを記載してください。
- `main` ブランチには直接pushせず、必ずPull Requestを経由してください。
- 詳しいルールは [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) を参照してください。

## 今後の拡張予定

この基盤の本来の目的に沿って、Webサイトに限らず以下のような種類のプロジェクトを
今後追加していく想定です（サンプルプロジェクトの拡張ではなく、基盤の活用範囲そのもの）。

- ニュース収集機能
- Web操作（ブラウジング・スクレイピングなど）機能
- 通知機能（Slack / Discord など）
- 定期実行・自動処理機能

MY DEVELOPMENT ARCHIVE（自分の開発記録）についても、以下のような拡張を想定しています。

- GitHub APIからのコミット・Pull Request自動取得
- AIによる開発履歴の自動要約
- 開発時間・AI別作業量・プロジェクト別の統計
- 年表表示、「去年の今日何を作っていたか」表示

## ライセンス

未定（プロジェクトの方向性が固まり次第、追記します）。
