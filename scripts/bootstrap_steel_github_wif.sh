#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ID="${PROJECT_ID:-rss7-ai-media}"
REGION="${REGION:-us-central1}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-oosaka0123-sudo/ai-agent}"
POOL_ID="${STEEL_GITHUB_WIF_POOL:-github-actions-ai-agent}"
PROVIDER_ID="${STEEL_GITHUB_WIF_PROVIDER:-steel-main}"
DEPLOYER_SA_NAME="${STEEL_GITHUB_DEPLOYER_SA:-github-actions-steel-deployer}"
RUNTIME_SA="${STEEL_BROWSER_RUNTIME_SA:-steel-browser-mcp@${PROJECT_ID}.iam.gserviceaccount.com}"
ARTIFACT_REPO="${STEEL_BROWSER_ARTIFACT_REPO:-cloud-run-source-deploy}"
WORKFLOW_PATH=".github/workflows/steel-browser-acceptance.yml"
REPO_DIR="${AI_AGENT_REPO_DIR:-$HOME/ai-agent}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

for cmd in gcloud git curl; do
  command -v "$cmd" >/dev/null 2>&1 || fail "$cmd is required"
done

active_account="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n1)"
[[ -n "$active_account" ]] || fail "an authenticated gcloud account is required"

gcloud config set project "$PROJECT_ID" >/dev/null
project_number="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
[[ -n "$project_number" ]] || fail "could not resolve project number"

printf '[1/7] Ensuring required identity APIs are enabled...\n'
gcloud services enable iamcredentials.googleapis.com sts.googleapis.com \
  --project="$PROJECT_ID" >/dev/null

printf '[2/7] Ensuring GitHub deployer service account exists...\n'
DEPLOYER_SA="${DEPLOYER_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe "$DEPLOYER_SA" \
  --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$DEPLOYER_SA_NAME" \
    --project="$PROJECT_ID" \
    --display-name="GitHub Actions Steel deployer"
fi

printf '[3/7] Ensuring Workload Identity Pool and GitHub provider exist...\n'
if ! gcloud iam workload-identity-pools describe "$POOL_ID" \
  --project="$PROJECT_ID" --location=global >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "$POOL_ID" \
    --project="$PROJECT_ID" --location=global \
    --display-name="ai-agent GitHub Actions"
fi

ATTRIBUTE_MAPPING="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref,attribute.workflow_ref=assertion.workflow_ref"
ATTRIBUTE_CONDITION="assertion.repository=='${GITHUB_REPOSITORY}' && assertion.ref=='refs/heads/main' && assertion.workflow_ref=='${GITHUB_REPOSITORY}/${WORKFLOW_PATH}@refs/heads/main' && (assertion.event_name=='push' || assertion.event_name=='workflow_dispatch')"

if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
  --project="$PROJECT_ID" --location=global \
  --workload-identity-pool="$POOL_ID" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
    --project="$PROJECT_ID" --location=global \
    --workload-identity-pool="$POOL_ID" \
    --issuer-uri="https://token.actions.githubusercontent.com/" \
    --attribute-mapping="$ATTRIBUTE_MAPPING" \
    --attribute-condition="$ATTRIBUTE_CONDITION" \
    --display-name="ai-agent Steel main workflow"
else
  gcloud iam workload-identity-pools providers update-oidc "$PROVIDER_ID" \
    --project="$PROJECT_ID" --location=global \
    --workload-identity-pool="$POOL_ID" \
    --attribute-condition="$ATTRIBUTE_CONDITION" >/dev/null
fi

POOL_NAME="$(gcloud iam workload-identity-pools describe "$POOL_ID" \
  --project="$PROJECT_ID" --location=global --format='value(name)')"
PROVIDER_NAME="$(gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
  --project="$PROJECT_ID" --location=global \
  --workload-identity-pool="$POOL_ID" --format='value(name)')"
[[ -n "$POOL_NAME" && -n "$PROVIDER_NAME" ]] || fail "WIF resource names could not be resolved"

printf '[4/7] Granting least-privilege WIF and deployment permissions...\n'
gcloud iam service-accounts add-iam-policy-binding "$DEPLOYER_SA" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/${GITHUB_REPOSITORY}" \
  >/dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${DEPLOYER_SA}" \
  --role="roles/run.developer" \
  --condition=None >/dev/null

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${DEPLOYER_SA}" \
  --role="roles/serviceusage.serviceUsageConsumer" \
  --condition=None >/dev/null

gcloud artifacts repositories add-iam-policy-binding "$ARTIFACT_REPO" \
  --project="$PROJECT_ID" --location="$REGION" \
  --member="serviceAccount:${DEPLOYER_SA}" \
  --role="roles/artifactregistry.writer" >/dev/null

gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:${DEPLOYER_SA}" \
  --role="roles/iam.serviceAccountUser" >/dev/null

printf '[PASS] WIF provider: %s\n' "$PROVIDER_NAME"
printf '[PASS] deployer service account: %s\n' "$DEPLOYER_SA"

printf '[5/7] Updating local ai-agent main...\n'
if [[ ! -d "$REPO_DIR/.git" ]]; then
  git clone "https://github.com/${GITHUB_REPOSITORY}.git" "$REPO_DIR"
fi
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || fail "$REPO_DIR working tree must be clean"
git -C "$REPO_DIR" fetch --quiet origin main
git -C "$REPO_DIR" checkout main
git -C "$REPO_DIR" pull --ff-only origin main

printf '[6/7] Deploying current main to Steel Browser Cloud Run...\n'
(
  cd "$REPO_DIR"
  PROJECT_ID="$PROJECT_ID" REGION="$REGION" \
    bash scripts/redeploy_steel_browser_mcp.sh
)

printf '[7/7] Running the real 5-step Steel acceptance test...\n'
(
  cd "$REPO_DIR"
  PROJECT_ID="$PROJECT_ID" REGION="$REGION" \
    bash scripts/run_steel_acceptance_cloudshell.sh
)

printf 'BOOTSTRAP RESULT: WIF configured, Steel deployed, acceptance helper completed.\n'
printf 'Future matching main pushes can deploy through GitHub Actions without a long-lived GCP key.\n'
