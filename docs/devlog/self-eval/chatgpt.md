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
