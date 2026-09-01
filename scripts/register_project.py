#!/usr/bin/env python3
"""Register a project/site in the ai-agent control-plane registry.

This script is intentionally standard-library only so it can run in GitHub Actions
without extra dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_registry(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data.get("projects"), list):
        raise ValueError("registry must contain a projects array")
    return data


def validate_args(args: argparse.Namespace) -> None:
    if not SLUG_RE.fullmatch(args.slug):
        raise ValueError("slug must be lowercase kebab-case (example: new-site)")
    if not REPO_RE.fullmatch(args.repository):
        raise ValueError("repository must be in owner/name format")
    if args.public_url and not (
        args.public_url.startswith("https://") or args.public_url.startswith("http://")
    ):
        raise ValueError("public-url must start with https:// or http://")


def build_project(args: argparse.Namespace) -> dict:
    project = {
        "slug": args.slug,
        "name": args.name,
        "repository": args.repository,
        "status": "pending-auto-onboarding" if args.auto_onboard else "registered",
        "default_role": args.role,
        "copilot_review": "planned",
        "auto_onboard": args.auto_onboard,
        "media": {
            "enabled": not args.no_media,
            "provider": args.media_provider,
            "control_plane_project": "rss7-ai-media",
        },
    }
    if args.public_url:
        project["public_url"] = args.public_url
    return project


def upsert_project(registry: dict, project: dict, update: bool) -> tuple[dict, str]:
    projects = registry["projects"]
    for index, existing in enumerate(projects):
        if existing.get("slug") == project["slug"]:
            if not update:
                raise ValueError(
                    f"project '{project['slug']}' already exists; use --update to replace it"
                )
            projects[index] = project
            action = "updated"
            break
    else:
        projects.append(project)
        action = "added"

    registry["version"] = max(int(registry.get("version", 1)), 2)
    registry["updated"] = date.today().isoformat()
    registry.setdefault(
        "onboarding",
        {
            "enabled": True,
            "control_plane_repository": "oosaka0123-sudo/ai-agent",
            "default_media_project": "rss7-ai-media",
            "default_provider": "google",
            "fallback_provider": "higgsfield",
        },
    )
    return registry, action


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register a new project/site")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--public-url", default="")
    parser.add_argument("--role", default="web-pwa-production")
    parser.add_argument(
        "--media-provider",
        choices=("auto", "google", "higgsfield"),
        default="auto",
    )
    parser.add_argument("--no-media", action="store_true")
    parser.add_argument(
        "--no-auto-onboard",
        dest="auto_onboard",
        action="store_false",
        default=True,
    )
    parser.add_argument("--update", action="store_true")
    parser.add_argument(
        "--registry", default="projects/registry.json", help="registry path"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print result without writing"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        validate_args(args)
        path = Path(args.registry)
        registry = load_registry(path)
        project = build_project(args)
        registry, action = upsert_project(registry, project, args.update)
        rendered = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
        if args.dry_run:
            print(rendered, end="")
        else:
            path.write_text(rendered, encoding="utf-8")
            print(f"{action}: {args.slug} -> {args.repository}")
            print(
                "Next: push the registry change. Auto Site Onboarding will create "
                "an onboarding PR in the target repository when credentials are configured."
            )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
