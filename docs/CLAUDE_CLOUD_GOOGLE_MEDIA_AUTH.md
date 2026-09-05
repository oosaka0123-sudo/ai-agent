# Claude Code Cloud ↔ Google Media MCP authentication

## Purpose

Define the safe runtime boundary for using the shared `google-media` Remote HTTP MCP from Claude Code cloud sessions.

This document is about **runtime authentication only**. It does not replace project onboarding, `.mcp.json`, Cloud Run, Vertex AI, or the shared Google Media architecture documented in `GOOGLE_MEDIA_MCP.md`.

## Current architecture

```text
Claude Code cloud session
  -> target repo .mcp.json
  -> google-media Remote HTTP MCP
  -> existing Cloud Run service
  -> Vertex AI Imagen / Veo
  -> GCS
```

Project onboarding may distribute:

- `.ai-agent/project.json`
- `.ai-agent/README.md`
- `.ai-agent/google_media_mcp_preflight.sh`
- the merged `mcpServers.google-media` entry in `.mcp.json`

No credential value is distributed in Git.

## Important Claude Cloud constraint

Claude Code cloud environments currently do not provide a dedicated secrets store. Environment variables configured on a cloud environment are copied into ordinary session environment variables and are readable by commands running in that session. Therefore:

- do not commit `GOOGLE_MEDIA_MCP_TOKEN`
- do not print it in Claude chat, Issues, PRs, logs, screenshots, or shell output
- do not treat a shared long-lived bearer token stored in a broadly shared Claude cloud environment as the final security design
- do not copy the token into every repository

The existing bearer-token mechanism remains usable for controlled runtime verification, but credential provisioning is deliberately separate from onboarding.

## Network requirement for Claude Code cloud

Claude Code cloud environments have an outbound network policy. The default `Trusted` policy does not mean arbitrary `run.app` hosts are automatically reachable.

When the existing Google Media Cloud Run hostname is blocked by the selected Claude cloud environment, use the environment's network configuration rather than rebuilding Google Cloud infrastructure:

1. keep the existing Cloud Run service
2. configure a Claude cloud environment whose network policy permits the current Cloud Run hostname
3. preserve the package-manager/default allowlist if the project needs it
4. start a **new** cloud session after environment changes; running sessions do not reload environment configuration

Current shared endpoint host:

`google-media-mcp-518404402696.us-central1.run.app`

Do not broaden network access to `Full` merely to solve one hostname unless there is a reviewed need. Prefer the narrowest working allowlist.

## Connection sequence for an onboarded project

From the target repository root:

1. confirm current branch / current repository state
2. run `bash .ai-agent/google_media_mcp_preflight.sh`
3. require configuration, token-presence, `/healthz`, and `/readyz` checks to pass
4. in Claude Code, inspect native MCP status / tool list
5. confirm `generate_image` and `generate_video`
6. run one minimal `generate_image` call using the registered project slug
7. only after image success, run one minimal `generate_video` call
8. do not poll the video operation separately; the MCP server performs polling server-side

If a project was onboarded before the managed preflight existed, use that project's existing equivalent preflight until a normal reviewed onboarding synchronization PR eventually adds the managed file. Do not rerun onboarding just to perform a runtime smoke test.

## Failure classification

Do not repeat the same failed approach more than twice. Report only:

### OBSERVED
What was actually measured.

### BLOCKER
The first confirmed stop point, one of:

- project checkout / config
- MCP recognition
- runtime bearer credential
- Claude cloud network policy
- Cloud Run routing / allowed host
- Cloud Run readiness
- MCP tool discovery
- Vertex AI / model / quota / billing
- generated-media persistence

### REQUIRED ACTION
The smallest action that addresses the confirmed blocker. Do not rebuild the Google Cloud project, Cloud Run service, or Vertex AI path unless evidence specifically requires an infrastructure change.

## Future target state

The preferred long-term authentication design is a mechanism that does not require a broadly reusable long-lived bearer secret to live in Claude cloud environment variables. Candidate designs must be reviewed before implementation and should favor:

- OAuth-compatible Remote MCP authentication managed by the client, or
- narrowly scoped short-lived credentials minted through an authenticated broker

Requirements for any replacement:

- no secret committed to target repositories
- no per-site Google Cloud project or service
- automatic expiry / rotation where practical
- revocation without editing every project
- project identity/audit attribution retained
- current cost-safety limits retained
- migration compatible with existing `.mcp.json` onboarding

Until such a replacement is implemented and verified, do not claim bearer-token persistence is fully automated or secret-store-backed.
