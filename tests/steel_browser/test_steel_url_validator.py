"""Unit tests for URL safety and SSRF protection.
"""
from __future__ import annotations

import pytest

from mcp_server.steel_browser.url_validator import validate_url_safety


def test_valid_public_urls():
    assert validate_url_safety("https://example.com") == "https://example.com"
    assert validate_url_safety("http://www.google.com/search?q=test") == "http://www.google.com/search?q=test"
    assert validate_url_safety("https://docs.steel.dev/cookbook/mcp") == "https://docs.steel.dev/cookbook/mcp"


def test_invalid_scheme():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_url_safety("ftp://example.com/file")

    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_url_safety("file:///etc/passwd")

    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_url_safety("gopher://127.0.0.1")


def test_blocked_hosts():
    blocked = [
        "http://localhost",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://0.0.0.0",
        "http://[::1]",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
    ]
    for url in blocked:
        with pytest.raises(ValueError, match="SSRF protection"):
            validate_url_safety(url)


def test_private_ips():
    private = [
        "http://10.0.0.1/admin",
        "http://172.16.0.1/internal",
        "http://192.168.1.1/router",
        "http://169.254.1.1",
    ]
    for url in private:
        with pytest.raises(ValueError, match="SSRF protection"):
            validate_url_safety(url)


def test_empty_url():
    with pytest.raises(ValueError, match="URL must be a non-empty string"):
        validate_url_safety("")

    with pytest.raises(ValueError, match="URL must be a non-empty string"):
        validate_url_safety(None)
