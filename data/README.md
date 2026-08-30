# data/ — 開発記録データベース

このディレクトリが「MY DEVELOPMENT ARCHIVE（自分の開発記録）」サイトのデータ本体です。
`web/` のページはここにあるJSONを読み込んで表示しているだけなので、
**記録を増やしたいときはHTMLを触らず、このJSONファイルを編集してください。**

- `projects.json` — プロジェクト一覧（関西サーファーKSなど、プロジェクト単位の情報）
- `devlog.json` — 開発記録（1回の作業ごとの日記データ。トップページのタイムラインの元）

編集後にサイトへ反映する方法は [`../README.md`](../README.md) の
「開発記録アーカイブサイトの運用方法」を参照してください
（ローカル確認: `bash scripts/sync-site-data.sh`、公開: `main` へマージするとGitHub Actionsが自動反映）。

## projects.json のフィールド

```jsonc
{
  "slug": "next-bus-osaka",       // 半角英数字とハイフンのみ。URLやファイル名に使うのでユニークにする
  "emoji": "🚌",                   // 一覧カードの目印になる絵文字
  "name": "次バス大阪",             // プロジェクト名（日本語表示名）
  "startDate": "2026-01-10",       // 開始日 "YYYY-MM-DD"。不明なら null
  "status": "進行中",               // 進行中 / 完了 / 休止 / 実験中 / 情報未入力 など自由記述
  "summary": "大阪のバス時刻を...",  // 概要（1〜3文程度）
  "aiUsed": ["Claude Code", "ChatGPT"], // 使ったAI（トップページのAI一覧・絞り込みに使われる）
  "tech": ["PWA", "JavaScript"],   // 使用技術（トップページの技術一覧・絞り込みに使われる）
  "github": "https://github.com/...", // GitHubリポジトリURL。なければ null
  "website": "https://...",        // 公開URL。なければ null
  "screenshots": ["assets/screenshots/next-bus-osaka-01.png"], // web/ からの相対パスの配列
  "notes": null                     // 補足メモ。なければ null
}
```

そのプロジェクトに紐づく開発記録は、`devlog.json` 側の `project` フィールドに
このプロジェクトの `slug` を書くことで自動的に紐づきます（`projects.json` 側で
開発記録IDを管理する必要はありません）。

## devlog.json のフィールド

```jsonc
{
  "id": "2026-08-30-ai-agent-kickoff", // ユニークなID。基本は "日付-短い英語スラッグ"
  "date": "2026-08-30",                 // 作業日 "YYYY-MM-DD"
  "title": "AIエージェント開発環境を開始", // カード・詳細ページのタイトル
  "project": "ai-agent",                 // projects.json の slug と一致させる
  "purpose": "...",                      // 目的：何のためにやったか
  "whatMade": "...",                     // 何を作ったか
  "changes": ["変更したファイルや内容"],   // どこを変更したか（箇条書き）
  "aiUsed": ["Claude Code"],             // 使ったAI
  "services": ["GitHub"],                // 使ったサービス（GitHub, Vercel, LINE Notify など）
  "tech": ["GitHub Actions"],            // 使った技術
  "problems": "...",                     // 困ったこと
  "solutions": "...",                    // 解決方法
  "learnings": "...",                    // 学んだこと
  "images": ["assets/screenshots/xxx.png"], // 完成画像（web/ からの相対パス）
  "githubCommits": [{ "label": "コミット概要", "url": "https://github.com/.../commit/xxxxx" }],
  "pullRequests": [{ "label": "PRタイトル", "url": "https://github.com/.../pull/1" }],
  "relatedUrls": [{ "label": "公開ページ", "url": "https://..." }],
  "nextSteps": "...",                    // 次にやること
  "tags": ["AIエージェント", "GitHub"]     // 検索・絞り込み用の自由なタグ
}
```

### 新しい開発記録を追加する手順

1. `docs/devlog/YYYY-MM-DD.md` に、その日やったことをMarkdownでそのまま書く
   （書式は [`../docs/devlog/_template.md`](../docs/devlog/_template.md) を参照）。
2. 上の形式で `devlog.json` の配列に1件追記する（末尾にオブジェクトを追加するだけでよい）。
3. 新しいプロジェクトについての記録なら、`projects.json` にもプロジェクトを1件追加する。
4. `bash scripts/sync-site-data.sh` を実行し、ローカルでサイトを開いて表示を確認する。

詳しい運用ルール（Claude Codeなど、AIエージェントが作業後に自動でこれを行うルール）は
[`../AGENTS.md`](../AGENTS.md) の「開発記録の自動記録ルール」を参照してください。
