"""Vertex AI などのメディア生成AIを呼び出すための共通基盤。

`scripts/generate_media.py` から利用される。プロバイダ（Google Vertex AI など）を
追加するときは `providers/` にモジュールを追加し、CLI側の `PROVIDERS` に登録する。
"""
