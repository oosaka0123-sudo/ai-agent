"""src/media_gen/naming.py のテスト（ネットワーク接続不要）。"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from media_gen.naming import build_output_path, extension_for_mime  # noqa: E402


def test_build_output_path_creates_directory_and_unique_names(tmp_path):
    output_dir = tmp_path / "ai"
    path1 = build_output_path(output_dir, "image", "png")
    path2 = build_output_path(output_dir, "image", "png")

    assert output_dir.is_dir()
    assert path1.parent == output_dir
    assert path1.suffix == ".png"
    assert path1.name.startswith("image_")
    assert path1 != path2  # 同一秒内でも乱数で重複しない


def test_build_output_path_with_index_suffix(tmp_path):
    path = build_output_path(tmp_path, "video", "mp4", index=2)
    assert path.name.endswith("-2.mp4")


def test_extension_for_mime_known_types():
    assert extension_for_mime("image/png", "bin") == "png"
    assert extension_for_mime("image/jpeg", "bin") == "jpg"
    assert extension_for_mime("video/mp4", "bin") == "mp4"


def test_extension_for_mime_fallback_to_default():
    assert extension_for_mime(None, "png") == "png"
    assert extension_for_mime("application/x-unknown-type", "png") == "png"
