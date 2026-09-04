import argparse
import json
import unittest

from scripts.onboard_projects import (
    build_desired_files,
    build_manifest,
    merge_mcp_json,
    render_google_media_preflight,
    render_readme,
    select_projects,
)
from scripts.register_project import build_project, upsert_project, validate_args


class ProjectOnboardingTests(unittest.TestCase):
    def test_register_project_adds_auto_onboarding_defaults(self):
        args = argparse.Namespace(
            slug="demo-site",
            name="Demo Site",
            repository="owner/demo-site",
            public_url="https://example.com/",
            role="web-pwa-production",
            media_provider="auto",
            no_media=False,
            auto_onboard=True,
        )
        validate_args(args)
        project = build_project(args)
        registry = {"version": 1, "max_parallel_projects": 4, "projects": []}
        registry, action = upsert_project(registry, project, update=False)

        self.assertEqual(action, "added")
        self.assertEqual(registry["max_parallel_projects"], 4)
        self.assertTrue(registry["projects"][0]["auto_onboard"])
        self.assertEqual(registry["projects"][0]["media"]["provider"], "auto")
        self.assertEqual(registry["onboarding"]["default_media_project"], "rss7-ai-media")

    def test_duplicate_slug_requires_update(self):
        project = {
            "slug": "demo-site",
            "name": "Demo",
            "repository": "owner/demo",
        }
        registry = {"projects": [dict(project)]}
        with self.assertRaises(ValueError):
            upsert_project(registry, project, update=False)

    def test_select_projects_skips_unconnected_and_control_plane(self):
        registry = {
            "projects": [
                {
                    "slug": "pending",
                    "name": "Pending",
                    "repository": None,
                    "auto_onboard": True,
                },
                {
                    "slug": "control",
                    "name": "Control",
                    "repository": "owner/control",
                    "auto_onboard": False,
                },
                {
                    "slug": "site",
                    "name": "Site",
                    "repository": "owner/site",
                    "auto_onboard": True,
                },
            ]
        }
        selected = select_projects(registry)
        self.assertEqual([item["slug"] for item in selected], ["site"])

    def test_manifest_uses_shared_media_control_plane(self):
        registry = {
            "onboarding": {
                "control_plane_repository": "owner/ai-agent",
                "default_media_project": "rss7-ai-media",
                "fallback_provider": "higgsfield",
            }
        }
        project = {
            "slug": "site",
            "name": "Site",
            "repository": "owner/site",
            "default_role": "web-pwa-production",
            "media": {"enabled": True, "provider": "auto"},
        }
        manifest = build_manifest(project, registry)
        self.assertEqual(manifest["managed_by"], "owner/ai-agent")
        self.assertEqual(
            manifest["automation"]["media"]["control_plane_project"], "rss7-ai-media"
        )
        self.assertEqual(
            manifest["automation"]["media"]["fallback_provider"], "higgsfield"
        )
        self.assertFalse(manifest["automation"]["direct_main_push"])

    def test_media_onboarding_includes_generic_preflight(self):
        registry = {
            "onboarding": {
                "control_plane_repository": "owner/ai-agent",
                "google_media_mcp_url": "https://media.example.run.app/mcp",
            }
        }
        project = {
            "slug": "demo-site",
            "name": "Demo Site",
            "repository": "owner/demo-site",
            "media": {"enabled": True, "provider": "auto"},
        }

        desired = build_desired_files(project, registry)

        self.assertEqual(
            set(desired),
            {
                ".ai-agent/project.json",
                ".ai-agent/README.md",
                ".ai-agent/google_media_mcp_preflight.sh",
                ".mcp.json",
            },
        )
        preflight = desired[".ai-agent/google_media_mcp_preflight.sh"]
        self.assertIn(".ai-agent/project.json", preflight)
        self.assertIn("GOOGLE_MEDIA_MCP_TOKEN", preflight)
        self.assertNotIn("50plus", preflight)
        self.assertNotIn("Bearer ${GOOGLE_MEDIA_MCP_TOKEN}", preflight)
        self.assertIn("OBSERVED", preflight)
        self.assertIn("BLOCKER", preflight)
        self.assertIn("REQUIRED ACTION", preflight)

        readme = desired[".ai-agent/README.md"]
        self.assertIn("bash .ai-agent/google_media_mcp_preflight.sh", readme)
        self.assertIn("project_slug=demo-site", readme)

    def test_media_disabled_does_not_distribute_mcp_or_preflight(self):
        registry = {
            "onboarding": {
                "google_media_mcp_url": "https://media.example.run.app/mcp",
            }
        }
        project = {
            "slug": "no-media",
            "name": "No Media",
            "repository": "owner/no-media",
            "media": {"enabled": False},
        }

        desired = build_desired_files(project, registry)

        self.assertEqual(
            set(desired), {".ai-agent/project.json", ".ai-agent/README.md"}
        )
        self.assertNotIn("google_media_mcp_preflight.sh", desired[".ai-agent/README.md"])

    def test_mcp_merge_preserves_other_servers(self):
        registry = {
            "onboarding": {
                "google_media_mcp_url": "https://media.example.run.app/mcp",
            }
        }
        project = {
            "slug": "demo-site",
            "name": "Demo Site",
            "repository": "owner/demo-site",
            "media": {"enabled": True},
        }
        existing = json.dumps(
            {
                "mcpServers": {
                    "existing-server": {
                        "type": "http",
                        "url": "https://existing.example/mcp",
                    }
                }
            }
        )

        merged = merge_mcp_json(existing, project, registry)
        self.assertIsNotNone(merged)
        doc = json.loads(merged)
        self.assertIn("existing-server", doc["mcpServers"])
        self.assertIn("google-media", doc["mcpServers"])

    def test_preflight_template_never_contains_a_project_specific_slug(self):
        preflight = render_google_media_preflight()
        self.assertIn("PROJECT_SLUG", preflight)
        self.assertIn("project.slug", preflight)
        self.assertNotIn("50plus", preflight)

    def test_readme_without_mcp_does_not_claim_preflight_exists(self):
        project = {
            "slug": "demo-site",
            "name": "Demo Site",
            "repository": "owner/demo-site",
        }
        readme = render_readme(project, mcp_json_included=False)
        self.assertIn("not yet added", readme)
        self.assertNotIn("bash .ai-agent/google_media_mcp_preflight.sh", readme)


if __name__ == "__main__":
    unittest.main()
