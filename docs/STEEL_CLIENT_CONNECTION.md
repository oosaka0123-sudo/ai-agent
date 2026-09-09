# Steel Browser MCP Client Connection

This document defines the client-side connection pattern for the production Steel Browser Remote HTTP MCP.

## Goal

Use one cloud-hosted Steel Browser MCP from multiple AI clients without copying a long-lived bearer token into repositories or permanently storing it in a Windows user environment variable.

## Canonical architecture

```text
AI client (Codex / Claude Code / future ChatGPT plugin)
        |
        | process-scoped Authorization: Bearer <token>
        v
Steel Browser Remote HTTP MCP on Cloud Run
        |
        v
Steel Cloud Browser API

Google Secret Manager
        |
        | gcloud read at client launch / verification time
        v
process-scoped STEEL_BROWSER_MCP_TOKEN
```

The Cloud Run service and GitHub Actions acceptance workflow remain the production control plane. A local Windows machine is only an optional client, not an always-on dependency.

## Security model

- Source of truth for the MCP bearer token: Google Secret Manager.
- The bridge reads the token with authenticated `gcloud` and never prints it.
- The token exists only in the bridge process and child processes.
- The bridge restores/removes the process environment variables in `finally`.
- No token is written to `.mcp.json`, `.env`, GitHub, logs, or the Windows user environment.
- The public Cloud Run URL may be committed; it is not a credential.
- If Google authentication is unavailable or secret access fails, the bridge fails closed.

## Windows client bridge

Run from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/steel_client_bridge.ps1 -Mode verify
```

The verification mode performs these checks:

1. Reads the bearer token from Secret Manager without displaying it.
2. Verifies authenticated MCP tool discovery directly.
3. Ensures the Codex global `steel-browser` registration exists.
4. Runs Claude Code's MCP health check from this project.
5. Removes the process-scoped secret after verification.

## Client-specific behavior

### Codex

Codex uses a global streamable HTTP MCP registration whose bearer value is read from `STEEL_BROWSER_MCP_TOKEN`. The bridge creates the registration if it is missing, then launches Codex with the token only in the child process.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/steel_client_bridge.ps1 -Mode codex
```

Additional Codex arguments can follow the mode argument.

### Claude Code

Claude Code uses the repository-shared `.mcp.json`. The Steel URL has a committed production default, while the Authorization header continues to reference `STEEL_BROWSER_MCP_TOKEN`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/steel_client_bridge.ps1 -Mode claude
```

### ChatGPT

The production endpoint is already a valid Remote HTTP MCP. Direct ChatGPT attachment should use a ChatGPT plugin/custom integration that stores the bearer credential in the platform connection layer. Do not copy the token into chat messages. Until that account-side attachment exists, Codex/Claude remain the verified direct clients and GitHub Actions remains the cloud acceptance path.

## Failure and recovery

- `gcloud` missing: install/repair Google Cloud CLI before using the local bridge.
- Google login expired: re-authenticate the local Google account, then rerun the bridge.
- Secret access denied: fix IAM outside the bridge; do not paste the token into source files as a workaround.
- MCP 401: verify that the Secret Manager latest version is the intended active token.
- MCP tool mismatch: treat it as a deployment/version regression and use the production acceptance workflow.
- Local machine offline: cloud deployment and GitHub Actions acceptance continue to work; only the optional local client path is unavailable.

## Design boundary

This bridge is intentionally not a replacement for the production acceptance flow in `scripts/run_steel_acceptance_cloudshell.sh` and `.github/workflows/steel-browser-acceptance.yml`. Its job is only to connect an authenticated local AI client safely and reproducibly.
