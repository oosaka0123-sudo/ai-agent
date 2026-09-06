"""SSRF and URL safety validation for Steel Browser MCP requests.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.169.254",
    "metadata.google.internal",
}


def _is_ip_unsafe(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_url_safety(url: str) -> str:
    """Validates that a URL is safe to navigate to, blocking private IPs,
    localhost, cloud metadata endpoints, and non-HTTP(S) schemes.
    Returns the normalized URL if valid.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    url_str = url.strip()
    parsed = urlparse(url_str)

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(
            f"Invalid URL scheme '{parsed.scheme}'. Only 'http' and 'https' are allowed."
        )

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: missing hostname.")

    hostname_lower = hostname.lower()

    if hostname_lower in BLOCKED_HOSTS or hostname_lower.endswith(".internal"):
        raise ValueError(
            f"SSRF protection: Navigation to restricted host '{hostname}' is blocked."
        )

    # Check direct IP address
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if _is_ip_unsafe(ip):
            raise ValueError(
                f"SSRF protection: Navigation to restricted IP address '{ip}' is blocked."
            )
        return url_str
    except ValueError as exc:
        if "SSRF protection" in str(exc):
            raise
        # Not a raw IP address, proceed to DNS resolution

    # Resolve domain to check resolved IPs
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if _is_ip_unsafe(ip):
                raise ValueError(
                    f"SSRF protection: Resolved IP '{ip_str}' for domain '{hostname}' is restricted and blocked."
                )
    except socket.gaierror:
        # If domain resolution fails, let upstream handle connection error or reject
        pass

    return url_str
