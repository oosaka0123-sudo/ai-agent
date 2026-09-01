import argparse
import unittest

from scripts.onboard_projects import build_manifest, select_projects
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


if __name__ == "__main__":
    unittest.main()
