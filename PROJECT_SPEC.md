# PROJECT_SPEC.md

このリポジトリで実装済み・実装予定の機能仕様をまとめたドキュメントです。
AIエージェントは、作業完了前の自己レビュー（[`AGENTS.md`](AGENTS.md) の
「自己評価・品質保証」参照）で、この仕様との照合を行ってください。

新しい機能を追加したら、このファイルにも仕様を追記してください
（実装してから仕様を書く場合も、実装する前に仕様を書く場合もどちらでもよい。
ただし実装が完了した機能は必ずここに残す）。

## 1. リポジトリ全体の目的（本題）

- **本当の目的**: Claude Code / Gemini・Jules / OpenAI Codex の3AIが、GitHubを
  共通記憶として並行作業できるAIエージェント開発基盤を作ること。
  Web / PWA / API連携 / 自動化 / 調査 / 通知 / アプリなど、用途を問わず
  さまざまなプロジェクトをこの基盤の上にAIチームで作れるようにする。
- **Webサイト制作そのものが目的ではない**: 以下の第2章・第3章
  （MY DEVELOPMENT ARCHIVE、複数AI比較ガイド）は、この基盤が実際に機能するかを
  確かめるための**サンプルプロジェクト**であり、リポジトリの目的そのものではない。
- 秘密情報（APIキー等）を絶対にコミット・公開しないこと。
- `main` を壊さない安全な構成（作業ブランチ + PR）であること。
- 特定用途に固定せず、あとから（Webサイトに限らず）どんな種類のプロジェクトでも
  追加できる汎用構成であること。
- 会話履歴のないAIセッションでも、`README.md` → `AGENTS.md` → 本ファイルの順に
  読めば、目的・ルール・現状を理解して作業を再開できること
  （詳細は `README.md` の「初めてこのリポジトリを開くAIエージェントへ」参照）。

## 2. サンプルプロジェクト: MY DEVELOPMENT ARCHIVE（自分の開発記録）

> 以下は基盤の動作確認のために作られた最初のサンプルプロジェクトです。
> リポジトリの目的そのものではありません。

個人がこれまで行ってきた開発を、後からスマホで簡単に振り返るための
開発履歴データベース＋開発日記サイト。

### 必須要件

- サイト名「MY DEVELOPMENT ARCHIVE」、日本語表示名「自分の開発記録」を
  トップページの大きなタイトル・サブタイトルとして表示する。
- トップページに以下をすべて表示する: 現在までの開発件数、最近の開発、
  プロジェクト一覧、開発タイムライン、使用したAI一覧、使用技術一覧、
  検索ボックス、タグ（AI・技術）による絞り込み。
- 開発タイムラインは日付順のカード形式で、各カードから詳細ページを開ける。
- プロジェクト一覧はカード形式。各プロジェクトはプロジェクト名・開始日・
  現在の状態・概要・使用AI・使用技術・GitHub・Webサイト・スクリーンショット・
  開発履歴を表示できる構造を持つ。
- 開発記録詳細ページには、日付・タイトル・目的・何を作ったか・
  どこを変更したか・使ったAI・使ったサービス・使った技術・困ったこと・
  解決方法・学んだこと・完成画像・GitHubコミット・Pull Request・関連URL・
  次にやること、を表示する。
- AI別（Claude Code / ChatGPT / Codex / Gemini / その他）、技術別
  （HTML, CSS, JavaScript, Python, GitHub, GitHub Actions, PWA, Android,
  API, Cloudflare, Vercel, AI Agent）に絞り込める。
- スクリーンショットは `docs/screenshots/` に保存し、1つの開発記録に
  複数登録できる。画像をタップすると拡大表示される。
- 開発記録データはHTMLへ直接書き込まず、後から追加しやすいデータ形式
  （`data/projects.json` / `data/devlog.json`、および `docs/devlog/*.md`）で管理する。
- 開発作業完了後、`docs/devlog/YYYY-MM-DD.md` と `data/devlog.json` に
  自動的に記録するルールを持つ（[`AGENTS.md`](AGENTS.md) 参照）。
- デザインはスマホ最優先・モダンで高級感のあるダークテーマ・カードUI・
  タイムライン・レスポンシブ・大きめの文字・見やすい余白。PCでも見やすいこと。
- 最初はHTML/CSS/JavaScript中心の静的サイトとして構築し、GitHub Pagesで
  公開できる構成にする。

### 実装場所

- `web/index.html`（トップページ）, `web/project.html`（プロジェクト詳細）,
  `web/devlog.html`（開発記録詳細）
- `data/projects.json`, `data/devlog.json`, `data/README.md`
- `docs/devlog/`（Markdown日記）, `docs/screenshots/`（画像）

### 将来拡張（未実装・仕様のみ）

- GitHub APIからのコミット・Pull Request自動取得
- AIによる開発履歴の自動要約
- 開発時間・AI別作業量・プロジェクト別の統計
- 年表表示、「去年の今日何を作っていたか」表示

## 3. サンプルプロジェクト: 複数AI比較ガイド（guides/）

> こちらも基盤の動作確認のために作られたサンプルプロジェクトです
> （3AIが同じ基盤の上で独立して並行作業できることを確かめる実例）。
> リポジトリの目的そのものではありません。

「3つのAIに同じサイトを別々に作らせる」のではなく、**1つの共通サイトの
トップページから、同じ開発テーマについて Claude Code / Gemini・Jules / Codex
の説明を選んで読めるサイト**。

### 必須要件

- サイト全体のUI・ナビゲーション・データ構造は共通化する。
- テーマを選ぶと、「Claude Codeの説明を見る」「Gemini / Julesの説明を見る」
  「Codexの説明を見る」の3つの選択肢を表示する。
- 各AIの説明ファイルは独立したファイルに分離する
  （推奨構成: `guides/<テーマID>/{claude,gemini,codex}.md`）。
- 各AIは自分が担当するファイルだけを編集し、他AIのファイルは変更・参考にしない
  （比較実験としての独立性を保つため）。共通UI（HTML/CSS/JS、`themes.json`、
  `theme.json`）はどのAIが編集してもよい。
- 各説明ページで扱う項目（共通テンプレート、[`guides/_template.md`](guides/_template.md)）:
  この方法の特徴・必要なサービス・スマホでの手順・GitHubリポジトリ作成・
  AIとの接続・HTML/CSS作成・GitHubへの保存・公開方法・初心者が迷いやすい点・
  メリット・デメリット・費用・PCが必要か・最終的に何ができるか。
- あとからテーマを追加できる構造にする（例: スマホでPWAを作る、
  スマホでAndroidアプリを作る、AIエージェントを作る、GitHub Pagesで公開する、
  GitHubを3つのLLMで共同利用する）。各テーマについて毎回、
  Claude Code / Gemini・Jules / Codex の3つの説明を選べるようにする。

### 第1テーマ: 「スマホだけでホームページを作る」

- テーマID: `smartphone-website`
- 2026-08-30時点のステータス: 3AIとも本文は未執筆（共通テンプレートの
  見出し構成のみ用意したプレースホルダー）。

### 実装場所

- `guides/themes.json`, `guides/<テーマID>/theme.json`,
  `guides/<テーマID>/{claude,gemini,codex}.md`
- `web/guides/index.html`（テーマ一覧）, `theme.html`（3AI選択）,
  `view.html`（説明表示、独自の軽量Markdownレンダラーで描画）

## 4. 全体で共通のインフラ

- `web/` は GitHub Pages の公開フォルダ。`data/`・`guides/`・
  `docs/screenshots/` が正本で、`scripts/sync-site-data.sh` が
  ビルド時に `web/data/`・`web/guides-data/`・`web/assets/screenshots/`
  へコピーする（`.gitignore` でコピー先は除外）。
- `.github/workflows/pages.yml` が `main` へのpushでこのスクリプトを実行し、
  GitHub Pagesへ自動デプロイする。

## 5. AIチーム運用基盤（本題そのもの）

サンプルプロジェクトではなく、このリポジトリの本題にあたる運用基盤。
詳細は各ファイルを参照（ここでは一覧のみ）。

- **オンボーディング**: 会話履歴のないAIセッションが最初に読む順番
  （`README.md` → `AGENTS.md` → `PROJECT_SPEC.md` → 自分のAI別ファイル →
  `docs/DEVELOPMENT.md` → `docs/devlog/`）。[`README.md`](README.md) 参照。
- **AI別の補足ファイル**: [`CLAUDE.md`](CLAUDE.md) / [`GEMINI.md`](GEMINI.md) /
  [`CODEX.md`](CODEX.md)。各AIの固有の注意点のみを書き、共通ルールは
  `AGENTS.md` に集約する。
- **自律実行ルール**: 明確な仕様がある作業は、途中で確認を挟まず
  実装からPush・報告まで自分で完了させる（[`AGENTS.md`](AGENTS.md) 参照）。
- **自己評価・品質保証ルール**: 各AIが自分の成果物について、本仕様との照合・
  自己レビュー・実動作テスト・自己採点・修正・再テストを行い、
  `docs/devlog/self-eval/<AI名>.md` に記録する。他AIの担当ファイルは
  変更・参考にしない（[`AGENTS.md`](AGENTS.md) 参照）。
- **開発記録の自動記録ルール**: 作業完了ごとに `docs/devlog/YYYY-MM-DD.md` と
  `data/devlog.json` に記録し、利用者向けの変更は `CHANGELOG.md` にも残す
  （[`AGENTS.md`](AGENTS.md) 参照）。
- **ブランチ・PRルール**: `main` へ直接pushせず作業ブランチ + PRで進める。
  秘密情報は `.env`（gitignore済み）にのみ記載する（[`AGENTS.md`](AGENTS.md)、
  [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) 参照）。
