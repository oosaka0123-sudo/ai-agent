"""Tests for the .mcp.json distribution added to onboard_projects.py.

Merge semantics matter here specifically because, unlike .ai-agent/*,
.mcp.json is not a file this control plane exclusively owns -- a target
repository may already have other MCP servers configured in it.
"""
import json
import unittest

from scripts.onboard_projects import merge_mcp_json

_REGISTRY_WITH_URL = {
    "onboarding": {
        "google_media_mcp_url": "https://google-media-mcp-abc123-uc.a.run.app/mcp",
    }
}

_REGISTRY_WITHOUT_URL = {"onboarding": {}}

_MEDIA_ENABLED = {"media": {"enabled": True, "provider": "auto"}}
_MEDIA_DISABLED = {"media": {"enabled": False, "provider": "auto"}}


class McpJsonMergeTests(unittest.TestCase):
    def test_creates_new_file_when_none_exists(self):
        result = merge_mcp_json(None, _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        doc = json.loads(result)
        self.assertIn("google-media", doc["mcpServers"])
        entry = doc["mcpServers"]["google-media"]
        self.assertEqual(entry["type"], "http")
        self.assertIn("https://google-media-mcp-abc123-uc.a.run.app/mcp", entry["url"])
        self.assertEqual(entry["headers"]["Authorization"], "Bearer ${GOOGLE_MEDIA_MCP_TOKEN}")

    def test_url_supports_env_override_with_default(self):
        result = merge_mcp_json(None, _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        url = json.loads(result)["mcpServers"]["google-media"]["url"]
        self.assertEqual(url, "${GOOGLE_MEDIA_MCP_URL:-https://google-media-mcp-abc123-uc.a.run.app/mcp}")

    def test_preserves_unrelated_existing_mcp_servers(self):
        existing = json.dumps({"mcpServers": {"some-other-tool": {"type": "http", "url": "https://example.com/mcp"}}})
        result = merge_mcp_json(existing, _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        doc = json.loads(result)
        self.assertIn("some-other-tool", doc["mcpServers"])
        self.assertIn("google-media", doc["mcpServers"])
        self.assertEqual(doc["mcpServers"]["some-other-tool"]["url"], "https://example.com/mcp")

    def test_preserves_unrelated_top_level_keys(self):
        existing = json.dumps({"mcpServers": {}, "someFutureTopLevelKey": {"x": 1}})
        result = merge_mcp_json(existing, _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        doc = json.loads(result)
        self.assertEqual(doc["someFutureTopLevelKey"], {"x": 1})

    def test_updates_existing_google_media_entry_in_place(self):
        existing = json.dumps(
            {"mcpServers": {"google-media": {"type": "http", "url": "https://old-url.example/mcp"}}}
        )
        result = merge_mcp_json(existing, _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        doc = json.loads(result)
        self.assertIn("google-media-mcp-abc123-uc.a.run.app", doc["mcpServers"]["google-media"]["url"])

    def test_media_disabled_returns_none_when_no_existing_file(self):
        self.assertIsNone(merge_mcp_json(None, _MEDIA_DISABLED, _REGISTRY_WITH_URL))

    def test_media_disabled_preserves_existing_file_unchanged(self):
        existing = json.dumps({"mcpServers": {"some-other-tool": {"type": "http", "url": "https://example.com/mcp"}}})
        result = merge_mcp_json(existing, _MEDIA_DISABLED, _REGISTRY_WITH_URL)
        doc = json.loads(result)
        self.assertNotIn("google-media", doc.get("mcpServers", {}))
        self.assertIn("some-other-tool", doc["mcpServers"])

    def test_no_mcp_url_configured_yet_returns_none_when_no_existing_file(self):
        # The control plane hasn't been deployed yet (human step not done),
        # so onboarding must not write a broken/placeholder URL.
        self.assertIsNone(merge_mcp_json(None, _MEDIA_ENABLED, _REGISTRY_WITHOUT_URL))

    def test_no_mcp_url_configured_yet_preserves_existing_file(self):
        existing = json.dumps({"mcpServers": {"some-other-tool": {}}})
        result = merge_mcp_json(existing, _MEDIA_ENABLED, _REGISTRY_WITHOUT_URL)
        self.assertEqual(json.loads(result), json.loads(existing))

    def test_malformed_existing_json_does_not_crash_and_still_adds_entry(self):
        result = merge_mcp_json("{not valid json", _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        doc = json.loads(result)
        self.assertIn("google-media", doc["mcpServers"])

    def test_running_twice_is_idempotent(self):
        first = merge_mcp_json(None, _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        second = merge_mcp_json(first, _MEDIA_ENABLED, _REGISTRY_WITH_URL)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
