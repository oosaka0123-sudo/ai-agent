# ChatGPT self-evaluation

## 2026-09-01 — Auto Site Onboarding

### 初回実装

新規サイトをcontrol-planeへ登録し、target repositoryへ管理manifestをPRで配布する
汎用オンボーディングを実装した。

### 自己評価

**92/100**

- 仕様適合性: 95
- 安全性: 96
- 保守性: 94
- 自動化: 92
- 実運用確認: 82

### 発見した問題と対策

- GitHubの標準 `GITHUB_TOKEN` は他リポジトリへ書けない。
  - 対策: cross-repo書き込みは `CONTROL_PLANE_GITHUB_TOKEN` に分離し、未設定時はcheckのみ。
- 将来サイト数が4を超える可能性がある。
  - 対策: `max_parallel_projects=4` を同時実行上限と定義し、登録総数には制限を設けない。
- 各サイトにGoogle認証をコピーすると秘密管理が破綻する。
  - 対策: target repoにはmanifestだけを置き、生成基盤・認証はcontrol-planeへ集中。
- 自動化が本番へ直行すると事故になる。
  - 対策: onboardingも公開もpreview/PR-firstを既定にした。

### テスト

標準ライブラリのみで、project登録・重複防止・onboarding対象選定・
shared media manifestの生成をunit test化した。

### 残課題

- 実際のcross-repo PR作成は、ユーザーが1回だけGitHub Secretを設定後に実地確認が必要。
- Higgsfieldは接続前なのでfallback設定は予約状態。

## 2026-09-05 — 50PLUS temporary Pages preview bridge

### 初回実装

50PLUS自身のGitHub PagesがRepository設定未有効で、現在のGitHub App接続からは管理設定を書き換えられないため、すでにPagesが有効な `ai-agent` を一時プレビュー母艦として使う方式を実装した。

Pages build時に公開Repository `oosaka0123-sudo/50plus` の最新 `main` をread-onlyで取得し、公開に必要な7 HTMLページと `assets/` のみを `web/50plus/` に一時生成する。生成物はコミットせず、全HTMLへ `noindex,nofollow` を注入してからPages artifactへ含める。

### 初回自己評価

**94/100**

- 仕様適合性: 96
- 安全性: 98
- 保守性: 91
- 自動化: 94
- 実運用確認: 93

### 発見した問題と修正

- 50PLUS専用Pagesを直接有効化するにはRepository管理権限が必要だった。
  - `REPO_FACTORY_TOKEN` を値非表示で確認したが未設定だったため、権限拡張やSecret作成は行わず別方式へ切り替えた。
- Preview copyが検索対象になる可能性がある。
  - artifact生成時に7ページすべてへ `noindex,nofollow` を強制し、生成後にも存在チェックを追加した。
- ai-agent側へ50PLUSソースを二重保存するとSSOTが壊れる。
  - `git clone` はActions runnerの一時領域だけで行い、`web/50plus/` もartifact生成時だけ作成する設計にした。
- feature branchでの動作確認後もbranch deployが残ると不要な公開経路になる。
  - 実走成功後、正式定義は `main` のみをpush対象に戻した。

### 実動作テスト

専用feature branchから実際のPages workflowを実行し、以下を確認した。

- 既存ai-agent Pages設定検証: success
- 50PLUS `main` clone: success
- 7 HTMLページ生成: success
- CSS / JavaScript存在確認: success
- 全HTMLの `noindex,nofollow` 確認: success
- Pages artifact upload: success
- GitHub Pages deploy: success (`Reported success`)
- 既存ai-agent公開artifactも同時に保持されていることをartifact一覧で確認

### 最終自己評価

**97/100**

残る制約は、50PLUS専用の `https://oosaka0123-sudo.github.io/50plus/` ではなく、一時的に `https://oosaka0123-sudo.github.io/ai-agent/50plus/` を使う点。完成後は予定どおりLolipopの `https://50plus.rss7.net` へ移行し、このbridgeを削除する。
