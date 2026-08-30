# GPT GitHub Control

このリポジトリでは、ChatGPT/GPT が GitHub コネクタ経由でブランチ作成、ファイル編集、PR作成、マージ、Issue作成、Actions再実行などを行える。

さらに `.github/workflows/gpt-ops.yml` により、GPT は Issue を作るだけで定型運用を実行できる。

## Issue コマンド

- `[GPT-OPS] deploy-pages`
  - `main` を取得
  - `scripts/sync-site-data.sh` を実行
  - GitHub Pages 用アーティファクトを作成
  - GitHub Pages へデプロイ
  - 成功時に Issue へ公開URLをコメント

- `[GPT-OPS] health-check`
  - `main` を取得
  - 公開データ同期
  - 主要ファイル存在確認
  - 成功時に Issue へ結果をコメント

## GPTが現在できる主な操作

- ブランチ作成
- テキストファイル作成・更新・削除
- PR作成・更新・マージ
- Issue作成・更新
- Actionsの失敗ジョブ再実行
- GPT Ops Issue経由のPages再デプロイ・ヘルスチェック

## 人間の操作が残る管理設定

GitHub/ChatGPTの現在の接続仕様上、次のようなリポジトリ管理設定はGPTから直接変更できない場合がある。

- リポジトリのPrivate/Public変更
- Default branch変更
- GitHub Pagesの初回有効化・Source変更
- GitHub App自体の権限変更
- アカウント認証が必要な設定変更

これらは初回だけ人間が設定し、その後の日常運用はGPT側へ寄せる。
