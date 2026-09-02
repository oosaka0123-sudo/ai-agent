#!/usr/bin/env python3
"""Create a client GitHub repository from a small JSON payload.

Designed for the issue-driven repository factory workflow. Uses only the
standard library and never prints the supplied token.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_payload(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data


def validate(payload: dict) -> dict:
    slug = str(payload.get("slug", "")).strip()
    name = str(payload.get("name", "")).strip()
    visibility = str(payload.get("visibility", "private")).strip().lower()
    description = str(payload.get("description", "")).strip()
    public_url = str(payload.get("public_url", "")).strip()
    media_provider = str(payload.get("media_provider", "auto")).strip().lower()

    if not SLUG_RE.fullmatch(slug):
        raise ValueError("slug must be lowercase kebab-case")
    if not name:
        raise ValueError("name is required")
    if visibility not in {"private", "public"}:
        raise ValueError("visibility must be private or public")
    if public_url and not public_url.startswith(("https://", "http://")):
        raise ValueError("public_url must start with http:// or https://")
    if media_provider not in {"auto", "google", "higgsfield"}:
        raise ValueError("media_provider must be auto, google, or higgsfield")

    return {
        "slug": slug,
        "name": name,
        "visibility": visibility,
        "description": description,
        "public_url": public_url,
        "media_provider": media_provider,
    }


def request(token: str, method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-agent-client-repo-factory",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code}: {detail}") from exc


def create_repo(token: str, owner: str, cfg: dict) -> dict:
    me = request(token, "GET", "https://api.github.com/user")
    login = str(me.get("login", ""))
    if owner == login:
        endpoint = "https://api.github.com/user/repos"
    else:
        endpoint = f"https://api.github.com/orgs/{owner}/repos"

    body = {
        "name": cfg["slug"],
        "description": cfg["description"] or f"Client website project: {cfg['name']}",
        "private": cfg["visibility"] == "private",
        "auto_init": True,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False,
    }
    return request(token, "POST", endpoint, body)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--payload", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--token", required=True)
    p.add_argument("--output", default="")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        cfg = validate(load_payload(Path(args.payload)))
        repo = create_repo(args.token, args.owner, cfg)
        full_name = repo.get("full_name") or f"{args.owner}/{cfg['slug']}"
        html_url = repo.get("html_url", "")
        values = {
            "slug": cfg["slug"],
            "name": cfg["name"],
            "repository": full_name,
            "url": html_url,
            "public_url": cfg["public_url"],
            "media_provider": cfg["media_provider"],
        }
        if args.output:
            with Path(args.output).open("a", encoding="utf-8") as fh:
                for key, value in values.items():
                    fh.write(f"{key}={value}\n")
        print(f"created: {full_name}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
