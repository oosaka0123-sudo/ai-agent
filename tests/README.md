# tests/

自動テストコードを配置するディレクトリです。

`src/` のディレクトリ構成に合わせてテストを配置してください。
テストの実行方法が決まったら、このREADMEと `.github/workflows/ci.yml` を更新してください。

## media_gen/（Python / pytest）

`src/media_gen/`（`scripts/generate_media.py` が使うVertex AIメディア生成基盤）の
単体テストです。実際のGoogle Cloudへ接続する部分（`providers/google_provider.py`）は
課金・認証情報が必要なため対象外とし、ファイル命名・リトライ・ログ記録などの
ネットワーク接続不要な処理のみをテストしています。

```bash
pip install -r requirements.txt
pytest tests/media_gen
```

CI（`.github/workflows/ci.yml`）でも同じコマンドを実行しています。

**注意**: このディレクトリ名を `media_gen` にしたのは `src/media_gen/` に合わせているため。
`tests/media_gen/` に `__init__.py` は置かないこと（pytestのデフォルトのimport modeでは、
`src/media_gen` と同名のパッケージとして解決されてしまい、`src/media_gen` の方が
import できなくなる）。
