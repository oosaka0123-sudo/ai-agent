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
PRELIGHT_TEMPLATE_PATH = Path(__file__).resolve().with_name(
    "google_media_mcp_preflight_template.sh"
)


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


def render_google_media_preflight() -> str:
    """Return the control-plane-owned generic connectivity preflight.

    The template contains no credential values and derives the target project slug
    from `.ai-agent/project.json` at runtime, so the same managed file can be
    distributed to every media-enabled project.
    """
    return PRELIGHT_TEMPLATE_PATH.read_text(encoding="utf-8")


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
    as-is (the original bytes, not a re-serialized equivalent -- returning
    `json.dumps(json.loads(existing_content))` here would still count as a
    "change" to onboard_project()'s plain string-equality diff, reformatting
    whatever the target repo's own JSON style was into a noisy no-op PR).
    """
    media = dict(project.get("media") or {})
    root = registry.get("onboarding", {})
    default_url = str(root.get("google_media_mcp_url", "")).strip()

    if not media.get("enabled", True) or not default_url:
        return existing_content if existing_content else None

    try:
        doc = json.loads(existing_content) if existing_content else {}
        if not isinstance(doc, dict):
            doc = {}
    except json.JSONDecodeError:
        # A target repo's malformed .mcp.json is that repo's problem to fix,
        # not something onboarding should crash over or silently discard --
        # but there's nothing safe to merge into, so leave it untouched too.
        return existing_content

    servers = doc.setdefault("mcpServers", {})
    servers["google-media"] = {
        "type": "http",
        "url": "${GOOGLE_MEDIA_MCP_URL:-" + default_url + "}",
        "headers": {"Authorization": "Bearer ${GOOGLE_MEDIA_MCP_TOKEN}"},
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def render_readme(project: dict, mcp_json_included: bool = False) -> str:
    name = project["name"]
    slug = project["slug"]
    if mcp_json_included:
        mcp_bullet = (
            "- Google Media MCP: `.mcp.json` (`mcpServers.google-media` entry only --\n"
            "  any other MCP servers already configured in this repository are left\n"
            "  untouched)\n"
            "- Google Media preflight: `.ai-agent/google_media_mcp_preflight.sh`"
        )
        mcp_section = (
            "The control plane provides shared AI media generation -- Google Vertex AI\n"
            "(Imagen / Veo) today, Higgsfield planned -- as a Remote HTTP MCP server, so\n"
            "Claude Code in this repository can call `generate_image` / `generate_video`\n"
            "directly. No generation code, Google Cloud project configuration, or actual\n"
            "credential value is copied into this repository: `.mcp.json` only configures\n"
            "how to reach the shared server -- its URL and an environment-variable-backed\n"
            "bearer token, resolved at run time rather than stored here."
        )
        setup_section = (
            "Before rebuilding or re-onboarding anything, run the managed connectivity\n"
            "preflight from the repository root:\n\n"
            "`bash .ai-agent/google_media_mcp_preflight.sh`\n\n"
            "It checks the existing config, token presence (never the value), network\n"
            "reachability, `/healthz`, and `/readyz`. If it passes, use Claude Code's\n"
            "native MCP status/tool list, run one minimal `generate_image` call for\n"
            f"`project_slug={slug}`, and only after image success run one minimal\n"
            "`generate_video` call. Do not poll video separately; the shared MCP handles\n"
            "that server-side.\n\n"
            "`.mcp.json`'s `Authorization` header reads `${GOOGLE_MEDIA_MCP_TOKEN}` from\n"
            "the Claude Code runtime environment. The value is never committed here.\n"
            "Cloud-hosted Claude environments currently have no dedicated secrets store,\n"
            "so credential provisioning remains a separate runtime concern; do not put\n"
            "the bearer value in repository files. See the control plane's\n"
            "`docs/GOOGLE_MEDIA_MCP.md` for the current authentication guidance."
        )
    else:
        mcp_bullet = (
            "- Google Media MCP: not yet added -- `.mcp.json` will arrive in a\n"
            "  follow-up PR once the control plane's MCP server is deployed (see\n"
            "  `docs/GOOGLE_MEDIA_MCP.md` in the control plane repository)"
        )
        mcp_section = (
            "The control plane will provide shared AI media generation -- Google Vertex\n"
            "AI (Imagen / Veo) today, Higgsfield planned -- as a Remote HTTP MCP server,\n"
            "so Claude Code in this repository will be able to call `generate_image` /\n"
            "`generate_video` directly, once a follow-up PR adds `.mcp.json` here. No\n"
            "generation code, Google Cloud project configuration, or actual credential\n"
            "value will be copied into this repository -- `.mcp.json` will only configure\n"
            "how to reach the shared server (its URL and an environment-variable-backed\n"
            "bearer token, resolved at run time rather than stored here)."
        )
        setup_section = (
            "Once the follow-up PR above adds `.mcp.json`, onboarding will also add the\n"
            "managed Google Media connectivity preflight under `.ai-agent/`. Runtime\n"
            "authentication remains separate and secret values must never be committed.\n"
            "See the control plane's `docs/GOOGLE_MEDIA_MCP.md` for the current setup."
        )
    return f"""# AI control-plane onboarding

This repository is registered with the shared AI control plane.

- Project: **{name}** (`{slug}`)
- Control plane: `oosaka0123-sudo/ai-agent`
- Managed manifest: `.ai-agent/project.json`
{mcp_bullet}
- Default publishing policy: **preview first**
- Direct push to `main`: **disabled**

## What becomes reusable automatically

{mcp_section}

Generation logs, provider routing, and future cross-project automation are
also shared this way, without copying implementation into every site.

## One-time setup this repository may still need

{setup_section}

## Safety boundary

This onboarding file and the managed preflight do not contain API keys,
service-account keys, passwords, or token values. Runtime credentials remain
outside repository content.

The control plane opens Pull Requests for managed changes. It does not directly
overwrite the production branch.
"""


def build_desired_files(
    project: dict,
    registry: dict,
    existing_mcp_json: str | None = None,
) -> dict[str, str]:
    """Build the complete target-repository onboarding payload.

    Control-plane-owned files stay under `.ai-agent/`. `.mcp.json` is the sole
    shared target file and is merged rather than replaced.
    """
    merged_mcp_json = merge_mcp_json(existing_mcp_json, project, registry)
    mcp_json_included = False
    if merged_mcp_json is not None:
        try:
            mcp_json_included = "google-media" in json.loads(merged_mcp_json).get(
                "mcpServers", {}
            )
        except json.JSONDecodeError:
            # Preserve malformed target JSON exactly as merge_mcp_json promises,
            # but do not claim Google Media is usable or distribute a preflight.
            mcp_json_included = False

    desired = {
        ".ai-agent/project.json": render_manifest(project, registry),
        ".ai-agent/README.md": render_readme(
            project, mcp_json_included=mcp_json_included
        ),
    }
    if mcp_json_included:
        desired[".ai-agent/google_media_mcp_preflight.sh"] = (
            render_google_media_preflight()
        )
    if merged_mcp_json is not None:
        desired[".mcp.json"] = merged_mcp_json
    return desired


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

    # .mcp.json is merged, not replaced wholesale (see merge_mcp_json) -- it
    # may already contain servers this control plane knows nothing about. In
    # --check mode there is no real API call to read the current file, so
    # the merge runs against "no existing file" -- fine, --check only
    # validates registry/onboarding logic locally, same as the other files.
    existing_mcp_json = None
    if apply:
        existing_mcp_json = decode_content(
            client.file(full_name, ".mcp.json", default_branch)
        )
    desired = build_desired_files(project, registry, existing_mcp_json)

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
            "It installs/updates control-plane-owned `.ai-agent/*` metadata and, when "
            "Google Media is enabled, safely merges only the `google-media` entry into "
            "`.mcp.json`. It does not deploy or publish anything and does not include "
            "credential values.\n"
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
