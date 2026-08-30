# GPT GitHub Control

このリポジトリでは、ChatGPT/GPT が GitHub コネクタ経由でブランチ作成、ファイル編集、PR作成、マージ、Issue作成、Actions再実行などを行える。

さらに `.github/workflows/gpt-ops.yml` と専用ブランチ `gpt-control` により、GPT は `.gpt-ops/command.txt` を更新するだけで定型運用を実行できる。

## GPT Ops コマンド

`gpt-control` ブランチの `.gpt-ops/command.txt` に次のどちらかを書き込む。

- `deploy-pages`
  - `main` を取得
  - `scripts/sync-site-data.sh` を実行
  - GitHub Pages 用アーティファクトを作成
  - GitHub Pages へデプロイ

- `health-check`
  - `main` を取得
  - 公開データ同期
  - 主要ファイル存在確認

GPTはGitHubコネクタから `gpt-control` ブランチのコマンドファイルを更新できるため、通常はユーザーがGitHub画面を操作する必要はない。

## GPTが現在できる主な操作

- ブランチ作成
- テキストファイル作成・更新・削除
- PR作成・更新・マージ
- Issue作成・更新
- Actionsの失敗ジョブ再実行
- GPT Ops経由のPages再デプロイ・ヘルスチェック

## 人間の操作が残る管理設定

GitHub/ChatGPTの現在の接続仕様上、次のようなリポジトリ管理設定はGPTから直接変更できない場合がある。

- リポジトリのPrivate/Public変更
- Default branch変更
- GitHub Pagesの初回有効化・Source変更
- GitHub App自体の権限変更
- アカウント認証が必要な設定変更

これらは初回だけ人間が設定し、その後の日常運用はGPT側へ寄せる。
