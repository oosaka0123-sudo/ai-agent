"""Remote HTTP MCP server exposing Google Vertex AI media generation
(Imagen / Veo) to every Claude Code project as shared tools.

This package is a thin, provider-routed wrapper around the existing
generation backend in ``src/media_gen`` (see PR #26) and is designed to be
deployed on Google Cloud Run. It does not reimplement image/video
generation; it adds the network boundary (MCP over streamable HTTP),
Google Cloud Storage persistence, audit logging, and cost-safety limits
around it.
"""
