import re

import pytest

from mcp_server.storage import build_gcs_object_path


def test_image_path_layout():
    path = build_gcs_object_path("rss7-house", "image", "image_20260901-120000_abcd1234.png")
    assert re.match(r"^projects/rss7-house/images/\d{4}/\d{2}/image_.+\.png$", path)


def test_video_path_layout():
    path = build_gcs_object_path("rss7-house", "video", "video_20260901-120000_abcd1234.mp4")
    assert re.match(r"^projects/rss7-house/videos/\d{4}/\d{2}/video_.+\.mp4$", path)


def test_unknown_media_type_raises():
    with pytest.raises(ValueError, match="unknown media_type"):
        build_gcs_object_path("rss7-house", "audio", "clip.mp3")
