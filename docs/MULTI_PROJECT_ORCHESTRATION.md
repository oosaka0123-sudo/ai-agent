# マルチプロジェクト並列運用

更新日: 2026-09-01

このリポジトリを複数プロジェクトの開発司令塔として使う。

## 対象

初期登録プロジェクト:

1. 関西サーファーKS
2. SリーグNOW
3. AIエージェントシステム
4. FX取引

今後のWebサイト・PWA・企業サイト・アプリ等も `projects/registry.json` へ追加する。
登録総数に4件という上限は設けない。`max_parallel_projects: 4` は同時に走らせる作業レーン数の上限である。

## 状態管理の正本

- 接続状態、運用状態、安全境界の正本は `projects/registry.json` とする。
- プロジェクト識別子は既存仕様に合わせて `slug` を使う。
- `data/projects.json` は MY DEVELOPMENT ARCHIVE の表示・紹介用データであり、運用状態の正本にはしない。
- 同じプロジェクトが `projects/registry.json` と `data/projects.json` の両方に存在する場合、`slug` は必ず一致させる。
- リポジトリ接続状況やCopilot監督状態を更新する場合は、まず `projects/registry.json` を更新する。
- 新規サイトの標準追加手順は [`AUTO_SITE_ONBOARDING.md`](AUTO_SITE_ONBOARDING.md) を正本とする。

## 基本運用

- 最大4プロジェクトを同時進行する。登録プロジェクト総数には上限を設けない。
- 1プロジェクトにつき原則1つのGitHubリポジトリを正本にする。
- Claude Code / Codex / Julesは実装担当として使う。
- GitHub Copilot ProはPRの一次監督・レビュー担当として使う。
- ChatGPTは全体設計、作業分割、優先順位、GitHub操作の統括を担当する。
- mainへ直接pushしない。各作業はブランチ→PR→レビュー→マージの順で進める。
- 自動マージは標準では使わない。最終マージ判断は人間に残す。
- 画像・動画生成はサイトごとに実装を複製せず、`ai-agent` の共有メディア基盤を再利用する。

## 並列レーン

各プロジェクトは独立レーンとして扱い、別プロジェクトの作業を同じブランチへ混ぜない。
レーンA〜Dは「現在同時に動かしている4件」を表し、固定プロジェクト名ではない。

## 新規サイトの自動オンボーディング

新規サイトはスマホから **Register Site** workflow または `scripts/register_project.py` で登録する。

登録PRがmainへ入ると **Auto Site Onboarding** workflow が動き、接続済みのtarget repositoryへ
`.ai-agent/project.json` と `.ai-agent/README.md` を追加する専用PRを自動作成する。

- target repoのmainへ直接pushしない
- Google/Higgsfield認証情報はtarget repoへコピーしない
- Google Vertex AIの共通projectは `rss7-ai-media`
- media providerの標準は `auto`
- Googleを主力、Higgsfieldは接続後のfallback/別モデル用途
- production公開は `preview-first` を既定とする

cross-repo PR作成には1回だけ `CONTROL_PLANE_GITHUB_TOKEN` のGitHub Secret設定が必要。
未設定時はcheckだけ実行し、安全に停止する。

## Copilot Proの役割

各プロジェクトで次を行う。

- 新規PRの自動レビュー
- 仕様違反、競合、古いブランチ、セキュリティ、CI失敗の検出
- Web/PWAでは390px前後のスマホUXを重点確認
- 問題があれば実装担当AIへ修正を戻す
- 問題がなければマージ候補として提示する

AI Credits節約のため、標準では「PRを開いた時の1回レビュー」を基本とし、
pushごとの自動再レビューは必要時だけ使う。

## 既存外部プロジェクトのオンボーディング

関西サーファーKS、SリーグNOW、FX取引などrepositoryが未接続の登録済みプロジェクトは、
GitHubリポジトリが見えるようになった時点で `repository` を更新する。
`auto_onboard: true` のプロジェクトは、次回workflow実行で自動オンボーディング対象になる。

必要に応じて各target repositoryへ以下の監督セットも導入する。

1. `.github/copilot-instructions.md`
2. `.github/skills/code-review/SKILL.md`
3. `.github/workflows/copilot-auto-review.yml`
4. `AGENTS.md` または既存の共通AIルール
5. ブランチ/PR運用

## FX安全境界

FX取引では、開発自動化と実売買を分離する。

- 自動化してよい: データ取得、分析、シグナル検証、バックテスト、ペーパートレード、レポート生成
- 人間の明示承認が必要: 実口座への注文、ポジション変更、資金移動、APIキー/権限変更
- PRが緑でも実売買を自動実行する設計にはしない
- メディア生成は既定で無効

## 現在の状態

- AIエージェントシステム: control-plane / Copilot自動レビュー稼働済み
- Auto Site Onboarding: 実装済み、cross-repo token設定後に実地稼働
- 関西サーファーKS: リポジトリ接続待ち
- SリーグNOW: リポジトリ接続待ち
- FX取引: リポジトリ接続待ち
