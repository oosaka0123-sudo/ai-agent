"""Unit tests for SessionTracker TTL and session lifecycle.
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock

from mcp_server.steel_browser.session_manager import SessionTracker


def test_session_tracker_register_touch_unregister():
    tracker = SessionTracker()
    info = tracker.register("sess_1", "proj_a", debug_url="https://debug")

    assert info.session_id == "sess_1"
    assert info.project_slug == "proj_a"
    assert info.status == "active"

    time.sleep(0.01)
    prev_active = info.last_active_at
    tracker.touch("sess_1")
    assert info.last_active_at > prev_active

    unregistered = tracker.unregister("sess_1")
    assert unregistered.status == "released"
    assert tracker.get("sess_1") is None


def test_session_tracker_inactivity_cleanup():
    tracker = SessionTracker()
    mock_client = MagicMock()

    info = tracker.register("sess_idle", "proj_a")
    # Simulate idleness
    info.last_active_at = time.time() - 100

    expired = tracker.cleanup_expired(mock_client, inactivity_timeout_sec=50, max_timeout_sec=500)
    assert "sess_idle" in expired
    assert tracker.get("sess_idle") is None
    mock_client.sessions.release.assert_called_with("sess_idle")


def test_session_tracker_max_timeout_cleanup():
    tracker = SessionTracker()
    mock_client = MagicMock()

    info = tracker.register("sess_old", "proj_a")
    # Simulate old creation
    info.created_at = time.time() - 1000
    info.last_active_at = time.time()  # active recently, but overall too old

    expired = tracker.cleanup_expired(mock_client, inactivity_timeout_sec=300, max_timeout_sec=500)
    assert "sess_old" in expired
    assert tracker.get("sess_old") is None
    mock_client.sessions.release.assert_called_with("sess_old")


def test_session_tracker_release_all():
    tracker = SessionTracker()
    mock_client = MagicMock()

    tracker.register("sess_1", "proj_a")
    tracker.register("sess_2", "proj_b")

    tracker.release_all(mock_client)
    assert len(tracker.list_active()) == 0
    assert mock_client.sessions.release.call_count == 2
