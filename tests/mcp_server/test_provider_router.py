import pytest

from mcp_server.provider_router import ProviderUnavailableError, resolve_provider_name


def test_auto_resolves_to_google():
    assert resolve_provider_name("auto") == "google"


def test_explicit_google_resolves_to_google():
    assert resolve_provider_name("google") == "google"


def test_higgsfield_is_a_named_not_yet_implemented_error():
    with pytest.raises(ProviderUnavailableError, match="not yet implemented"):
        resolve_provider_name("higgsfield")


def test_unknown_provider_raises_clear_error():
    with pytest.raises(ProviderUnavailableError, match="unknown provider"):
        resolve_provider_name("totally-made-up-provider")
