"""In-memory session manager for Steel Cloud Browser sessions.

Tracks active sessions, enforces inactivity and lifetime TTLs, and handles cleanup.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger("mcp_server.steel_browser.session_manager")


@dataclass
class SessionInfo:
    session_id: str
    project_slug: str
    created_at: float
    last_active_at: float
    debug_url: Optional[str] = None
    last_url: Optional[str] = None
    status: str = "active"

    def touch(self, url: Optional[str] = None) -> None:
        self.last_active_at = time.time()
        if url:
            self.last_url = url


class SessionTracker:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionInfo] = {}

    def register(
        self,
        session_id: str,
        project_slug: str,
        debug_url: Optional[str] = None,
    ) -> SessionInfo:
        now = time.time()
        info = SessionInfo(
            session_id=session_id,
            project_slug=project_slug,
            created_at=now,
            last_active_at=now,
            debug_url=debug_url,
            status="active",
        )
        self._sessions[session_id] = info
        logger.info("Registered Steel session %s for project %s", session_id, project_slug)
        return info

    def get(self, session_id: str) -> Optional[SessionInfo]:
        return self._sessions.get(session_id)

    def touch(self, session_id: str, url: Optional[str] = None) -> Optional[SessionInfo]:
        info = self._sessions.get(session_id)
        if info and info.status == "active":
            info.touch(url)
        return info

    def unregister(self, session_id: str) -> Optional[SessionInfo]:
        info = self._sessions.pop(session_id, None)
        if info:
            info.status = "released"
            logger.info("Unregistered Steel session %s", session_id)
        return info

    def list_active(self) -> list[SessionInfo]:
        return [s for s in self._sessions.values() if s.status == "active"]

    def cleanup_expired(
        self,
        steel_client: Any,
        inactivity_timeout_sec: float,
        max_timeout_sec: float,
    ) -> list[str]:
        now = time.time()
        expired_ids: list[str] = []

        for session_id, info in list(self._sessions.items()):
            if info.status != "active":
                continue

            idle_time = now - info.last_active_at
            total_time = now - info.created_at

            if idle_time > inactivity_timeout_sec or total_time > max_timeout_sec:
                expired_ids.append(session_id)
                info.status = "expired"
                logger.info(
                    "Session %s expired (idle: %.1fs, total: %.1fs). Releasing upstream.",
                    session_id,
                    idle_time,
                    total_time,
                )
                try:
                    if hasattr(steel_client, "sessions") and hasattr(steel_client.sessions, "release"):
                        steel_client.sessions.release(session_id)
                except Exception as exc:
                    logger.warning("Failed to release expired Steel session %s: %s", session_id, exc)
                self._sessions.pop(session_id, None)

        return expired_ids

    def release_all(self, steel_client: Any) -> None:
        for session_id, info in list(self._sessions.items()):
            logger.info("Releasing session %s during teardown", session_id)
            try:
                if hasattr(steel_client, "sessions") and hasattr(steel_client.sessions, "release"):
                    steel_client.sessions.release(session_id)
            except Exception as exc:
                logger.warning("Failed to release Steel session %s during teardown: %s", session_id, exc)
            self._sessions.pop(session_id, None)
