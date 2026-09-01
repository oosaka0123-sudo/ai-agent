#!/usr/bin/env python3
"""Open idempotent onboarding PRs for registered projects.

The control plane never pushes directly to a target repository's default branch.
It creates a dedicated branch, writes only managed .ai-agent/* files, and opens a PR.

Cross-repository writes require a fine-grained GitHub token in
CONTROL_PLANE_GITHUB_TOKEN. Without a token, --check still validates the registry.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def load_registry(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data.get("projects"), list):
        raise ValueError("registry must contain a projects array")
    return data


def select_projects(registry: dict, slug: str | None = None) -> list[dict]:
    selected: list[dict] = []
    for project in registry["projects"]:
        if slug and project.get("slug") != slug:
            continue
        if not project.get("auto_onboard", False):
            continue
        repo = project.get("repository")
        if not repo:
            continue
        if not REPO_RE.fullmatch(repo):
            raise ValueError(f"invalid repository for {project.get('slug')}: {repo}")
        selected.append(project)
    if slug and not selected:
        raise ValueError(f"no auto-onboardable project found for slug '{slug}'")
    return selected


def build_manifest(project: dict, registry: dict) -> dict:
    root = registry.get("onboarding", {})
    media = dict(project.get("media") or {})
    media.setdefault("enabled", True)
    media.setdefault("provider", "auto")
    media.setdefault(
        "control_plane_project", root.get("default_media_project", "rss7-ai-media")
    )
    media.setdefault("fallback_provider", root.get("fallback_provider", "higgsfield"))
    return {
        "version": 1,
        "managed_by": root.get(
            "control_plane_repository", "oosaka0123-sudo/ai-agent"
        ),
        "project": {
            "slug": project["slug"],
            "name": project["name"],
            "repository": project["repository"],
            "public_url": project.get("public_url"),
            "role": project.get("default_role", "web-pwa-production"),
        },
        "automation": {
            "media": media,
            "publish_policy": project.get("publish_policy", "preview-first"),
            "direct_main_push": False,
        },
    }


def render_manifest(project: dict, registry: dict) -> str:
    return json.dumps(build_manifest(project, registry), ensure_ascii=False, indent=2) + "\n"


def merge_mcp_json(existing_content: str | None, project: dict, registry: dict) -> str | None:
    """Adds/updates only the `mcpServers.google-media` entry, preserving every
    other key and every other MCP server already in the target repository's
    own `.mcp.json` untouched -- unlike `.ai-agent/*`, this file is not
    exclusively owned by the control plane, so it is merged, never replaced
    wholesale.

    Returns None when there is nothing to write: media generation is
    disabled for this project, or the control plane has not been deployed
    yet (`onboarding.google_media_mcp_url` unset in the registry) -- either
    way, a project with no existing `.mcp.json` gets no file at all rather
    than an empty one, and a project that already has one keeps it exactly
    as-is.
    """
    media = dict(project.get("media") or {})
    root = registry.get("onboarding", {})
    default_url = str(root.get("google_media_mcp_url", "")).strip()

    try:
        doc = json.loads(existing_content) if existing_content else {}
        if not isinstance(doc, dict):
            doc = {}
    except json.JSONDecodeError:
        # A target repo's malformed .mcp.json is that repo's problem to fix,
        # not something onboarding should crash over or silently discard.
        doc = {}

    if not media.get("enabled", True) or not default_url:
        if not doc:
            return None
        return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"

    servers = doc.setdefault("mcpServers", {})
    servers["google-media"] = {
        "type": "http",
        "url": "${GOOGLE_MEDIA_MCP_URL:-" + default_url + "}",
        "headers": {"Authorization": "Bearer ${GOOGLE_MEDIA_MCP_TOKEN}"},
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def render_readme(project: dict) -> str:
    name = project["name"]
    slug = project["slug"]
    return f"""# AI control-plane onboarding

This repository is registered with the shared AI control plane.

- Project: **{name}** (`{slug}`)
- Control plane: `oosaka0123-sudo/ai-agent`
- Managed manifest: `.ai-agent/project.json`
- Google Media MCP: `.mcp.json` (`mcpServers.google-media` entry only --
  any other MCP servers already configured in this repository are left
  untouched)
- Default publishing policy: **preview first**
- Direct push to `main`: **disabled**

## What becomes reusable automatically

The control plane provides shared AI media generation -- Google Vertex AI
(Imagen / Veo) today, Higgsfield planned -- as a Remote HTTP MCP server, so
Claude Code in this repository can call `generate_image` / `generate_video`
directly. No generation code, credentials, or Google Cloud project
configuration is copied into this repository: `.mcp.json` only points at
the shared server's URL.

Generation logs, provider routing, and future cross-project automation are
also shared this way, without copying implementation into every site.

## One-time setup this repository may still need

`.mcp.json`'s `Authorization` header reads `${{GOOGLE_MEDIA_MCP_TOKEN}}` from
the environment Claude Code runs in -- it is never committed here. Set it
once wherever this repository's Claude Code sessions run. See the control
plane's `docs/GOOGLE_MEDIA_MCP.md` for where to get the value.

## Safety boundary

This onboarding file does not contain API keys, service-account keys, passwords,
or tokens. Credentials remain in the control plane / GitHub Secrets.

The control plane opens Pull Requests for managed changes. It does not directly
overwrite the production branch.
"""


class GitHubError(RuntimeError):
    pass


@dataclass
class GitHubClient:
    token: str
    api_url: str = "https://api.github.com"

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        url = self.api_url.rstrip("/") + path
        data = None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-agent-control-plane",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GitHubError(f"GitHub API {exc.code} {method} {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"GitHub API connection failed: {exc}") from exc

    def repo(self, full_name: str) -> dict:
        return self.request("GET", f"/repos/{full_name}")

    def open_pulls(self, full_name: str) -> list[dict]:
        return self.request("GET", f"/repos/{full_name}/pulls?state=open&per_page=100")

    def onboarding_pr(self, full_name: str, slug: str) -> dict | None:
        prefix = f"ai-onboarding/{slug}-"
        for pr in self.open_pulls(full_name):
            if pr.get("head", {}).get("ref", "").startswith(prefix):
                return pr
        return None

    def ref_sha(self, full_name: str, branch: str) -> str:
        encoded = urllib.parse.quote(f"heads/{branch}", safe="/")
        return self.request("GET", f"/repos/{full_name}/git/ref/{encoded}")["object"]["sha"]

    def create_branch(self, full_name: str, branch: str, sha: str) -> None:
        self.request(
            "POST",
            f"/repos/{full_name}/git/refs",
            {"ref": f"refs/heads/{branch}", "sha": sha},
        )

    def file(self, full_name: str, path: str, ref: str) -> dict | None:
        encoded = urllib.parse.quote(path, safe="/")
        try:
            return self.request(
                "GET",
                f"/repos/{full_name}/contents/{encoded}?ref={urllib.parse.quote(ref)}",
            )
        except GitHubError as exc:
            if " 404 " in str(exc):
                return None
            raise

    def put_file(
        self,
        full_name: str,
        path: str,
        content: str,
        branch: str,
        current_sha: str | None,
    ) -> None:
        encoded = urllib.parse.quote(path, safe="/")
        payload: dict[str, Any] = {
            "message": f"chore: sync AI onboarding ({path})",
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if current_sha:
            payload["sha"] = current_sha
        self.request("PUT", f"/repos/{full_name}/contents/{encoded}", payload)

    def open_pr(
        self, full_name: str, title: str, head: str, base: str, body: str
    ) -> dict:
        return self.request(
            "POST",
            f"/repos/{full_name}/pulls",
            {"title": title, "head": head, "base": base, "body": body},
        )


def decode_content(file_info: dict | None) -> str | None:
    if not file_info:
        return None
    if file_info.get("encoding") != "base64":
        return None
    return base64.b64decode(file_info["content"]).decode("utf-8")


def onboard_project(
    client: GitHubClient,
    project: dict,
    registry: dict,
    apply: bool,
) -> str:
    full_name = project["repository"]
    repo_info = client.repo(full_name) if apply else {"default_branch": "main"}
    default_branch = repo_info.get("default_branch", "main")

    desired = {
        ".ai-agent/project.json": render_manifest(project, registry),
        ".ai-agent/README.md": render_readme(project),
    }

    # .mcp.json is merged, not replaced wholesale (see merge_mcp_json) -- it
    # may already contain servers this control plane knows nothing about. In
    # --check mode there is no real API call to read the current file, so
    # the merge runs against "no existing file" -- fine, --check only
    # validates registry/onboarding logic locally, same as the other files.
    existing_mcp_json = None
    if apply:
        existing_mcp_json = decode_content(client.file(full_name, ".mcp.json", default_branch))
    merged_mcp_json = merge_mcp_json(existing_mcp_json, project, registry)
    if merged_mcp_json is not None:
        desired[".mcp.json"] = merged_mcp_json

    if not apply:
        return f"check: {project['slug']} -> {full_name} ({len(desired)} managed files)"

    changed = False
    for path, content in desired.items():
        info = client.file(full_name, path, default_branch)
        if decode_content(info) != content:
            changed = True

    if not changed:
        return f"up-to-date: {project['slug']} -> {full_name}"

    existing_pr = client.onboarding_pr(full_name, project["slug"])
    if existing_pr:
        branch = existing_pr["head"]["ref"]
        pr_url = existing_pr.get("html_url", full_name)
        result_prefix = "pr-updated"
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        branch = f"ai-onboarding/{project['slug']}-{stamp}"
        base_sha = client.ref_sha(full_name, default_branch)
        client.create_branch(full_name, branch, base_sha)
        pr_url = ""
        result_prefix = "pr-opened"

    for path, content in desired.items():
        info = client.file(full_name, path, branch)
        if decode_content(info) == content:
            continue
        client.put_file(
            full_name,
            path,
            content,
            branch,
            info.get("sha") if info else None,
        )

    if existing_pr:
        return f"{result_prefix}: {project['slug']} -> {pr_url}"

    pr = client.open_pr(
        full_name,
        "chore: AI control-plane onboarding",
        branch,
        default_branch,
        (
            "This PR was opened by the shared `ai-agent` control plane.\n\n"
            "It only installs/updates `.ai-agent/*` managed metadata so this project "
            "can reuse shared AI media and future automation. It does not deploy or "
            "publish anything and does not include credentials.\n"
        ),
    )
    return f"{result_prefix}: {project['slug']} -> {pr.get('html_url', full_name)}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Onboard registered projects")
    parser.add_argument("--registry", default="projects/registry.json")
    parser.add_argument("--project", default=None, help="only this project slug")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        registry = load_registry(Path(args.registry))
        projects = select_projects(registry, args.project)
        if not projects:
            print("No connected auto-onboardable projects. Nothing to do.")
            return 0

        if args.apply:
            token = os.environ.get("CONTROL_PLANE_GITHUB_TOKEN", "").strip()
            if not token:
                raise ValueError(
                    "CONTROL_PLANE_GITHUB_TOKEN is required for --apply "
                    "(fine-grained token: target repo Contents + Pull requests write)"
                )
            client = GitHubClient(token)
        else:
            client = GitHubClient("check-only")

        failures = 0
        for index, project in enumerate(projects):
            if index:
                time.sleep(0.2)
            try:
                print(onboard_project(client, project, registry, args.apply))
            except (GitHubError, ValueError, KeyError) as exc:
                failures += 1
                print(f"failed: {project.get('slug')}: {exc}", file=sys.stderr)

        return 1 if failures else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
