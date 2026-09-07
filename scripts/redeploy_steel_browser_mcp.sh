#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ID="${PROJECT_ID:-rss7-ai-media}"
REGION="${REGION:-us-central1}"
SERVICE="${STEEL_BROWSER_SERVICE:-steel-browser-mcp}"
ARTIFACT_REPO="${STEEL_BROWSER_ARTIFACT_REPO:-cloud-run-source-deploy}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

for cmd in git gcloud curl; do
  command -v "$cmd" >/dev/null 2>&1 || fail "$cmd is required"
done

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "run this inside the ai-agent repository"
cd "$repo_root"

[[ "$(git branch --show-current)" == "main" ]] || fail "main branch is required"
[[ -z "$(git status --porcelain)" ]] || fail "working tree must be clean"

git fetch --quiet origin main
local_sha="$(git rev-parse main)"
remote_sha="$(git rev-parse origin/main)"
[[ "$local_sha" == "$remote_sha" ]] || fail "local main must match origin/main"

active_account="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n1)"
[[ -n "$active_account" ]] || fail "an authenticated gcloud account is required"

project_number="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
[[ -n "$project_number" ]] || fail "could not resolve project number"

image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/${SERVICE}:${local_sha:0:12}"
before_revision="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --format='value(status.latestReadyRevisionName)')"

printf '[1/4] Building Steel Browser image from main...\n'
gcloud builds submit \
  --project="$PROJECT_ID" \
  --config=cloudbuild.steel-browser.yaml \
  --substitutions="_IMAGE=${image}" \
  .

printf '[2/4] Updating existing Cloud Run service image only...\n'
gcloud run services update "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --image="$image" \
  --quiet

after_revision="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --format='value(status.latestReadyRevisionName)')"
[[ -n "$after_revision" ]] || fail "no ready revision reported after deploy"
[[ "$after_revision" != "$before_revision" ]] || fail "Cloud Run ready revision did not change"
printf '[PASS] ready revision: %s\n' "$after_revision"

printf '[3/4] Checking /readyz...\n'
service_url="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --format='value(status.url)')"
[[ -n "$service_url" ]] || fail "could not resolve service URL"
ready_body="$(curl -fsS --connect-timeout 10 --max-time 30 "${service_url%/}/readyz")"
[[ "$ready_body" == *'"ready":true'* || "$ready_body" == *'"ready": true'* ]] || \
  fail "/readyz did not report ready=true"
printf '[PASS] /readyz ready=true\n'

printf '[4/4] Steel Browser MCP redeploy complete.\n'
printf 'RESULT: Steel Browser MCP source %s is deployed and ready.\n' "${local_sha:0:12}"
