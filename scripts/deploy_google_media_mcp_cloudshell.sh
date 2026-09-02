#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="rss7-ai-media"
REGION="us-central1"
SERVICE="google-media-mcp"
SA_NAME="google-media-mcp"
SA_EMAIL="${SA_NAME}@${PROJECT}.iam.gserviceaccount.com"
BUCKET="rss7-ai-media-genmedia"
SECRET="google-media-mcp-token"
AR_REPO="cloud-run-source-deploy"
WORKDIR="${HOME}/ai-agent-cloudrun"

echo "== Google Media MCP / Cloud Run deploy =="
gcloud config set project "${PROJECT}" >/dev/null

ACCOUNT="$(gcloud config get-value account 2>/dev/null)"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT}" --format='value(projectNumber)')"
echo "Project: ${PROJECT}"
echo "Account: ${ACCOUNT}"

# Required APIs.
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  --project="${PROJECT}" --quiet

# Runtime service account.
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${PROJECT}" \
    --display-name="Google Media MCP (Cloud Run)"
fi

gcloud projects add-iam-policy-binding "${PROJECT}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user" \
  --condition=None --quiet >/dev/null

# Generated-media bucket.
if ! gcloud storage buckets describe "gs://${BUCKET}" --project="${PROJECT}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET}" \
    --project="${PROJECT}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi

gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin" \
  --quiet >/dev/null

# Application bearer token. Never print the value.
if ! gcloud secrets describe "${SECRET}" --project="${PROJECT}" >/dev/null 2>&1; then
  openssl rand -hex 32 | gcloud secrets create "${SECRET}" \
    --project="${PROJECT}" \
    --replication-policy="automatic" \
    --data-file=- >/dev/null
else
  ENABLED_VERSION="$(gcloud secrets versions list "${SECRET}" \
    --project="${PROJECT}" --filter='state=ENABLED' \
    --format='value(name)' --limit=1 2>/dev/null || true)"
  if [[ -z "${ENABLED_VERSION}" ]]; then
    openssl rand -hex 32 | gcloud secrets versions add "${SECRET}" \
      --project="${PROJECT}" --data-file=- >/dev/null
  fi
fi

gcloud secrets add-iam-policy-binding "${SECRET}" \
  --project="${PROJECT}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet >/dev/null

# Artifact Registry repository used by Cloud Run source deploys.
if ! gcloud artifacts repositories describe "${AR_REPO}" \
  --project="${PROJECT}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${AR_REPO}" \
    --project="${PROJECT}" \
    --location="${REGION}" \
    --repository-format=docker \
    --description="Cloud Run source deployments" >/dev/null
fi

# The service account used by Cloud Build varies by project age/configuration.
for BUILD_SA in \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  "${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"; do
  if gcloud iam service-accounts describe "${BUILD_SA}" --project="${PROJECT}" >/dev/null 2>&1; then
    gcloud projects add-iam-policy-binding "${PROJECT}" \
      --member="serviceAccount:${BUILD_SA}" \
      --role="roles/run.builder" \
      --condition=None --quiet >/dev/null || true
  fi
done

# Fresh source checkout. The repository is public; no GitHub token is required.
rm -rf "${WORKDIR}"
git clone --depth 1 --branch main \
  https://github.com/oosaka0123-sudo/ai-agent.git "${WORKDIR}"
cd "${WORKDIR}"

test -f Dockerfile || { echo "ERROR: Dockerfile not found" >&2; exit 20; }

# Deploy. Cloud Run is publicly reachable because Claude Code clients generally
# do not possess a Google identity. The MCP server itself still requires the
# bearer token stored in Secret Manager, so billable generation is not open.
gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --source=. \
  --service-account="${SA_EMAIL}" \
  --allow-unauthenticated \
  --ingress=all \
  --port=8080 \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=0 \
  --timeout=600 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_MEDIA_GCS_BUCKET=${BUCKET},GOOGLE_MEDIA_MAX_IMAGE_COUNT=4,GOOGLE_MEDIA_MAX_VIDEO_DURATION_SECONDS=8,GOOGLE_MEDIA_MAX_RETRY_ATTEMPTS=2,GOOGLE_MEDIA_MAX_CONCURRENT_PER_PROJECT=1,GOOGLE_MEDIA_GLOBAL_MAX_CONCURRENT=0,LOG_LEVEL=INFO" \
  --set-secrets="GOOGLE_MEDIA_MCP_TOKEN=${SECRET}:latest" \
  --quiet

SERVICE_URL="$(gcloud run services describe "${SERVICE}" \
  --project="${PROJECT}" --region="${REGION}" \
  --format='value(status.url)')"
SERVICE_HOST="${SERVICE_URL#https://}"
SERVICE_HOST="${SERVICE_HOST%/}"

# Required by the MCP SDK's DNS-rebinding protection.
gcloud run services update "${SERVICE}" \
  --project="${PROJECT}" --region="${REGION}" \
  --update-env-vars="GOOGLE_MEDIA_MCP_ALLOWED_HOSTS=${SERVICE_HOST}" \
  --quiet >/dev/null

READY="NG"
for _ in $(seq 1 30); do
  if curl -fsS "${SERVICE_URL}/readyz" >/tmp/google-media-ready.json 2>/dev/null; then
    READY="OK"
    break
  fi
  sleep 3
done

echo
echo "========================================"
echo "DEPLOY COMPLETE"
echo "Cloud Run URL: ${SERVICE_URL}"
echo "MCP URL:       ${SERVICE_URL}/mcp"
echo "READY:         ${READY}"
if [[ -f /tmp/google-media-ready.json ]]; then
  printf 'readyz: '
  cat /tmp/google-media-ready.json
  echo
fi
echo "Token: stored in Secret Manager (${SECRET}); value not printed."
echo "========================================"
