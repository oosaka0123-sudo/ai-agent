# src/

アプリケーション本体のソースコードを配置するディレクトリです。

現時点では特定の用途（ニュース収集・Web操作・通知・自動処理など）に固定していません。
今後、具体的な機能を追加する際は、機能ごとにサブディレクトリを分けて配置してください。

例:
```
src/
├── news/       # ニュース収集機能を追加する場合
├── web/        # Web操作機能を追加する場合
├── notify/     # 通知機能を追加する場合
├── core/       # 共通処理・エージェントのコアロジック
└── media_gen/  # Vertex AIなどの画像・動画生成基盤（scripts/generate_media.py から利用）
```

## media_gen/

`scripts/generate_media.py` が使う画像・動画生成基盤です。

- `config.py` — `.env` からGoogle Cloudの設定（プロジェクトID・リージョン）を読み込む
- `naming.py` — 生成物の保存ファイル名（日時＋種類＋乱数）を組み立てる
- `logging_utils.py` — `logs/media-generation.jsonl` への実行結果の記録
- `retry.py` — 失敗時に1回だけ自動リトライする共通処理
- `providers/google_provider.py` — Google Vertex AI（Imagen / Veo）への接続実装

新しいプロバイダ（別のAI基盤など）を追加する場合は `providers/` にモジュールを追加し、
`scripts/generate_media.py` の `PROVIDERS` 辞書に登録してください。
