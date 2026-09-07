#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="rss7-ai-media"
REGION="us-central1"
SERVICE="google-media-mcp"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is required"
command -v gcloud >/dev/null 2>&1 || fail "gcloud is required"
command -v curl >/dev/null 2>&1 || fail "curl is required"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "run this inside the ai-agent repository"
cd "$repo_root"

[[ -f Dockerfile ]] || fail "Dockerfile not found at repository root"
grep -q "Google Media MCP Server" Dockerfile || fail "root Dockerfile is not the Google Media MCP image"

branch="$(git branch --show-current)"
[[ "$branch" == "main" ]] || fail "switch to main before deployment (current: ${branch:-detached})"

[[ -z "$(git status --porcelain)" ]] || fail "working tree is not clean; commit/stash changes before deployment"

git fetch --quiet origin main
local_head="$(git rev-parse HEAD)"
remote_head="$(git rev-parse origin/main)"
[[ "$local_head" == "$remote_head" ]] || fail "local main is not current origin/main; pull/rebase first"

active_account="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n1)"
[[ -n "$active_account" ]] || fail "no active gcloud account; authenticate in Cloud Shell first"
printf 'Using gcloud account: %s\n' "$active_account"
printf 'Deploying commit: %s\n' "$local_head"

before_revision="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.latestReadyRevisionName)')"
service_url="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)')"

[[ -n "$before_revision" ]] || fail "could not read current Cloud Run revision"
[[ -n "$service_url" ]] || fail "could not read Cloud Run service URL"

printf 'Current revision: %s\n' "$before_revision"
printf 'Service URL: %s\n' "$service_url"
printf '%s\n' 'Preserving existing service IAM, service account, environment variables and Secret Manager bindings.'

# Intentionally do NOT pass --set-env-vars, --set-secrets, --service-account,
# --allow-unauthenticated, or --no-allow-unauthenticated here. For an existing
# Cloud Run service, omitting those flags preserves the current service settings
# and IAM policy while deploying the current source image.
gcloud run deploy "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --source=. \
  --quiet

after_revision="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.latestReadyRevisionName)')"
service_url="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)')"

[[ -n "$after_revision" ]] || fail "deployment finished but no ready revision was reported"
printf 'Ready revision: %s\n' "$after_revision"

if [[ "$after_revision" == "$before_revision" ]]; then
  fail "Cloud Run revision did not change; deployment was not applied"
fi

ready_body="$(mktemp)"
trap 'rm -f "$ready_body"' EXIT
ready_status="$(curl -sS --connect-timeout 10 --max-time 30 \
  -o "$ready_body" -w '%{http_code}' "$service_url/readyz" || true)"
printf '/readyz HTTP status: %s\n' "$ready_status"
cat "$ready_body"
printf '\n'

[[ "$ready_status" == "200" ]] || fail "new revision is not ready over /readyz"
grep -Eq '"ready"[[:space:]]*:[[:space:]]*true' "$ready_body" || fail "/readyz did not report ready=true"

printf '%s\n' 'RESULT: Google Media MCP Cloud Run redeploy completed and /readyz is healthy.'
printf '%s\n' 'NEXT: start a NEW Claude Code session with the MCP-Cloud environment and verify google-media tool discovery before running generate_image/generate_video.'
