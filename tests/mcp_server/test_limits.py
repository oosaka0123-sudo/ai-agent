import json

import pytest

from mcp_server.config import Limits
from mcp_server.limits import (
    ConcurrencyGate,
    LimitError,
    load_global_max_concurrent,
    validate_image_count,
    validate_project_slug,
    validate_video_duration,
)


def test_valid_slugs_pass():
    for slug in ("rss7-house", "a", "site-2", "kansai-surfer-ks"):
        validate_project_slug(slug)  # must not raise


@pytest.mark.parametrize("slug", ["", "Bad_Slug", "has space", "UPPER", "trailing-", "-leading", "double--dash"])
def test_invalid_slugs_raise(slug):
    with pytest.raises(LimitError):
        validate_project_slug(slug)


def test_image_count_within_cap_passes():
    validate_image_count(4, Limits(max_image_count=4))


def test_image_count_over_cap_raises():
    with pytest.raises(LimitError, match="exceeds"):
        validate_image_count(5, Limits(max_image_count=4))


def test_image_count_below_one_raises():
    with pytest.raises(LimitError):
        validate_image_count(0, Limits())


def test_video_duration_within_cap_passes():
    validate_video_duration(8, Limits(max_video_duration_seconds=8))


def test_video_duration_over_cap_raises():
    with pytest.raises(LimitError, match="exceeds"):
        validate_video_duration(9, Limits(max_video_duration_seconds=8))


def test_video_duration_none_is_allowed():
    validate_video_duration(None, Limits())  # provider default; must not raise


def test_global_max_concurrent_env_override_wins(monkeypatch):
    assert load_global_max_concurrent(Limits(global_max_concurrent=7)) == 7


def test_global_max_concurrent_falls_back_to_registry(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps({"max_parallel_projects": 9}), encoding="utf-8")
    assert load_global_max_concurrent(Limits(global_max_concurrent=0), registry_path=registry_path) == 9


def test_global_max_concurrent_defaults_when_registry_missing(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    assert load_global_max_concurrent(Limits(global_max_concurrent=0), registry_path=missing) == 4


def test_concurrency_gate_blocks_over_per_project_cap():
    gate = ConcurrencyGate(global_max=10, per_project_max=1)
    gate.acquire("site-a")
    with pytest.raises(LimitError):
        gate.acquire("site-a")
    gate.release("site-a")
    gate.acquire("site-a")  # must succeed again after release


def test_concurrency_gate_allows_different_projects_independently():
    gate = ConcurrencyGate(global_max=10, per_project_max=1)
    gate.acquire("site-a")
    gate.acquire("site-b")  # different project, must not be blocked by site-a


def test_concurrency_gate_blocks_over_global_cap_even_across_projects():
    gate = ConcurrencyGate(global_max=1, per_project_max=5)
    gate.acquire("site-a")
    with pytest.raises(LimitError):
        gate.acquire("site-b")
