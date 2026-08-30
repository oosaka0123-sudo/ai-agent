# guides/ — 複数AI比較ガイド

このディレクトリは、**同じテーマについて Claude Code / Gemini・Jules / Codex がそれぞれ
独立して説明を書き、読者が3つを見比べられるガイド集**のデータです。

「3つのAIに同じサイトを別々に作らせる」ものではありません。
**サイトのUI・ナビゲーション・データ構造は共通**で、テーマごとに用意された
「説明文章（Markdown）」の部分だけを、AIごとに分けて書きます。

## 全体の仕組み

```
guides/
  themes.json                      # テーマ一覧（トップページに表示される）
  smartphone-website/               # 1つのテーマ = 1つのディレクトリ
    theme.json                      # テーマの情報 + 3AIの担当ファイル一覧
    claude.md                       # Claude Code が書く説明
    gemini.md                       # Gemini / Jules が書く説明
    codex.md                        # Codex が書く説明
```

サイト側（`web/guides/`）はこれらのJSON/Markdownを読み込んで表示するだけで、
説明文章そのものはHTMLに書きません。公開時は `scripts/sync-site-data.sh` が
このディレクトリを `web/guides-data/` へコピーします。

## 【最重要】担当ルール

- **各AIは、自分が担当する `.md` ファイルだけを編集してください。**
  - Claude Code → `claude.md`
  - Gemini / Jules → `gemini.md`
  - Codex → `codex.md`
- **他のAIが担当するファイルの中身は変更・参考にしないでください。**
  同じ条件・同じテーマで、独立して説明を書くことに意味があります。
- `themes.json` や `theme.json`、`web/guides/` 配下のHTML/CSS/JSといった
  **サイトの共通部分は、どのAIが編集してもかまいません**
  （新しいテーマを追加する、UIを改善する、など）。

## 新しいテーマを追加する手順

1. `guides/<テーマID>/` ディレクトリを作る（例: `guides/pwa-app/`）。
2. [`_template.md`](_template.md) を `claude.md` / `gemini.md` / `codex.md` としてコピーする
   （中身はまだ空でよい＝プレースホルダー）。
3. `guides/<テーマID>/theme.json` を作る（[`smartphone-website/theme.json`](smartphone-website/theme.json) を参考に）。
4. `guides/themes.json` にテーマを1件追加する。
5. `bash scripts/sync-site-data.sh` を実行してローカルで表示を確認する。

## 各説明ページに書く項目（共通テンプレート）

すべてのテーマ・すべてのAIで、以下の項目をそのAI自身の考え方で説明します
（[`_template.md`](_template.md) に見出しとして用意済み）。

- この方法の特徴 / 必要なサービス / スマホでの手順
- GitHubリポジトリ作成 / AIとの接続 / HTML/CSS作成 / GitHubへの保存 / 公開方法
- 初心者が迷いやすい点 / メリット / デメリット / 費用 / PCが必要か / 最終的に何ができるか
