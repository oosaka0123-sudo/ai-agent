"""GitHub Actions OIDC-authenticated Steel Browser acceptance runner."""
from __future__ import annotations

import os
from typing import Any

import jwt
from jwt import PyJWKClient

from .server import create_session, extract, navigate, release_session, screenshot

_GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
_GITHUB_JWKS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks"
_DEFAULT_AUDIENCE = "steel-browser-acceptance"
_DEFAULT_REPOSITORY = "oosaka0123-sudo/ai-agent"
_DEFAULT_REF = "refs/heads/main"
_DEFAULT_WORKFLOW = ".github/workflows/steel-browser-acceptance.yml"

_jwks_client = PyJWKClient(_GITHUB_JWKS_URL, cache_keys=True)


def _expected_claims() -> dict[str, str]:
    repository = os.environ.get(
        "STEEL_ACCEPTANCE_GITHUB_REPOSITORY", _DEFAULT_REPOSITORY
    ).strip()
    ref = os.environ.get("STEEL_ACCEPTANCE_GITHUB_REF", _DEFAULT_REF).strip()
    workflow_path = os.environ.get(
        "STEEL_ACCEPTANCE_GITHUB_WORKFLOW", _DEFAULT_WORKFLOW
    ).strip()
    audience = os.environ.get(
        "STEEL_ACCEPTANCE_GITHUB_AUDIENCE", _DEFAULT_AUDIENCE
    ).strip()
    return {
        "repository": repository,
        "ref": ref,
        "workflow_ref": f"{repository}/{workflow_path}@{ref}",
        "audience": audience,
    }


def verify_github_actions_oidc(token: str) -> dict[str, Any]:
    """Validate a GitHub Actions OIDC token and pin it to this repo/workflow/ref."""
    if not token:
        raise ValueError("missing bearer token")

    expected = _expected_claims()
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=expected["audience"],
        issuer=_GITHUB_ISSUER,
        options={
            "require": [
                "exp",
                "iat",
                "nbf",
                "iss",
                "aud",
                "repository",
                "ref",
                "workflow_ref",
                "event_name",
            ]
        },
    )

    if claims.get("repository") != expected["repository"]:
        raise ValueError("repository claim mismatch")
    if claims.get("ref") != expected["ref"]:
        raise ValueError("ref claim mismatch")
    if claims.get("workflow_ref") != expected["workflow_ref"]:
        raise ValueError("workflow_ref claim mismatch")
    if claims.get("event_name") != "workflow_dispatch":
        raise ValueError("event_name claim mismatch")

    return claims


def run_acceptance_lifecycle(
    *, project_slug: str = "rss7-ai-media", target_url: str = "https://example.com/"
) -> dict[str, Any]:
    """Run the 5-step real Steel lifecycle without returning sensitive payloads."""
    steps: list[dict[str, Any]] = []
    session_id: str | None = None
    failed_step = "create_session"
    primary_error: Exception | None = None

    try:
        created = create_session(project_slug=project_slug)
        session_id = created.get("session_id")
        if not session_id:
            raise RuntimeError("create_session returned no session_id")
        steps.append({"name": "create_session", "status": "pass"})

        failed_step = "navigate"
        navigated = navigate(session_id=session_id, url=target_url)
        if navigated.get("status") != "success":
            raise RuntimeError("navigate returned unexpected status")
        steps.append({"name": "navigate", "status": "pass"})

        failed_step = "extract"
        extracted = extract(session_id=session_id, format="text")
        text = extracted.get("content") or ""
        if not text.strip():
            raise RuntimeError("extract returned empty content")
        steps.append(
            {"name": "extract", "status": "pass", "content_chars": len(text)}
        )

        failed_step = "screenshot"
        captured = screenshot(session_id=session_id, full_page=False)
        image_b64 = captured.get("screenshot_base64") or ""
        if len(image_b64) < 100 or captured.get("mime_type") != "image/png":
            raise RuntimeError("screenshot returned no usable PNG payload")
        steps.append(
            {
                "name": "screenshot",
                "status": "pass",
                "base64_chars": len(image_b64),
                "mime_type": "image/png",
            }
        )
    except Exception as exc:
        primary_error = exc
    finally:
        if session_id:
            try:
                released = release_session(session_id=session_id)
                if released.get("status") != "released":
                    raise RuntimeError("release_session returned unexpected status")
                steps.append({"name": "release_session", "status": "pass"})
            except Exception as exc:
                if primary_error is None:
                    failed_step = "release_session"
                    primary_error = exc

    if primary_error is not None:
        return {
            "ok": False,
            "failed_step": failed_step,
            "error_type": type(primary_error).__name__,
            "steps": steps,
        }

    return {
        "ok": True,
        "target_url": target_url,
        "steps": steps,
        "result": "ALL_PASS",
    }
