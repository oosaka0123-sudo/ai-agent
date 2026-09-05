#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OBSERVED=()
BLOCKERS=()
ACTIONS=()

add_observed() { OBSERVED+=("$1"); }
add_blocker() { BLOCKERS+=("$1"); }
add_action() { ACTIONS+=("$1"); }

report_failure() {
  printf 'OBSERVED\n'
  printf -- '- %s\n' "${OBSERVED[@]}"
  printf 'BLOCKER\n'
  printf -- '- %s\n' "${BLOCKERS[@]}"
  printf 'REQUIRED ACTION\n'
  printf -- '- %s\n' "${ACTIONS[@]}"
}

for command in python3 curl; do
  if ! command -v "$command" >/dev/null 2>&1; then
    add_observed "$command is unavailable in the current Claude Code environment."
    add_blocker "Local preflight prerequisite is missing."
    add_action "Use a Claude Code environment with $command available; do not recreate Google Cloud resources."
    report_failure
    exit 1
  fi
done

if [[ ! -f .ai-agent/project.json || ! -f .mcp.json ]]; then
  add_observed "Required onboarding files are not both present in the checked-out repository root."
  add_blocker "The current checkout is not fully onboarded or is not the expected current branch."
  add_action "Fetch the current target repository branch and inspect existing onboarding files; do not recreate them automatically."
  report_failure
  exit 1
fi

CONFIG="$(python3 - <<'PY'
import json
from pathlib import Path

project = json.loads(Path('.ai-agent/project.json').read_text(encoding='utf-8'))
slug = project.get('project', {}).get('slug')
if not isinstance(slug, str) or not slug:
    raise SystemExit('missing project.slug')

mcp = json.loads(Path('.mcp.json').read_text(encoding='utf-8'))
server = mcp.get('mcpServers', {}).get('google-media')
if not isinstance(server, dict) or server.get('type') != 'http':
    raise SystemExit('missing google-media HTTP MCP entry')
url = server.get('url')
if not isinstance(url, str) or not url:
    raise SystemExit('missing google-media URL')
auth = (server.get('headers') or {}).get('Authorization', '')
if '${GOOGLE_MEDIA_MCP_TOKEN}' not in auth:
    raise SystemExit('Authorization is not environment-variable backed')
print(slug)
print(url)
PY
)" 2>/dev/null
CONFIG_RC=$?

if [[ $CONFIG_RC -ne 0 ]]; then
  add_observed "Existing onboarding/MCP files did not pass structural validation."
  add_blocker "Project or MCP configuration cannot be recognized safely."
  add_action "Inspect the existing files and current onboarding PR history. Do not overwrite .mcp.json or rerun onboarding blindly."
  report_failure
  exit 1
fi

PROJECT_SLUG="$(printf '%s\n' "$CONFIG" | sed -n '1p')"
RAW_MCP_URL="$(printf '%s\n' "$CONFIG" | sed -n '2p')"
add_observed "Project onboarding and google-media HTTP MCP configuration are present."

MCP_URL="$(RAW_MCP_URL="$RAW_MCP_URL" python3 - <<'PY'
import os, re
raw = os.environ['RAW_MCP_URL']
override = os.environ.get('GOOGLE_MEDIA_MCP_URL')
if override:
    print(override)
else:
    match = re.fullmatch(r'\$\{GOOGLE_MEDIA_MCP_URL:-([^}]+)\}', raw)
    print(match.group(1) if match else raw)
PY
)"

if [[ "$MCP_URL" != http://* && "$MCP_URL" != https://* ]]; then
  add_observed "The google-media URL did not resolve to HTTP(S)."
  add_blocker "MCP endpoint resolution failed."
  add_action "Inspect an intentional GOOGLE_MEDIA_MCP_URL override or the existing onboarding configuration; do not create a replacement service."
  report_failure
  exit 1
fi
add_observed "google-media endpoint URL resolved from existing configuration."

if [[ -n "${GOOGLE_MEDIA_MCP_TOKEN:-}" ]]; then
  add_observed "GOOGLE_MEDIA_MCP_TOKEN is present in this Claude Code environment (value not displayed)."
else
  add_observed "GOOGLE_MEDIA_MCP_TOKEN is not present in this Claude Code environment."
  add_blocker "Client bearer token is missing."
  add_action "Provide runtime authentication through the approved Claude Code execution environment without printing, committing, or logging the token value."
fi

BASE_URL="${MCP_URL%/}"
[[ "$BASE_URL" == */mcp ]] && BASE_URL="${BASE_URL%/mcp}"

probe() {
  local name="$1" url="$2" body code rc
  body="$(mktemp)"
  code="$(curl --silent --show-error --connect-timeout 5 --max-time 15 --output "$body" --write-out '%{http_code}' "$url" 2>/dev/null)"
  rc=$?

  if [[ $rc -ne 0 ]]; then
    add_observed "$name produced no usable HTTP response (curl exit $rc)."
    add_blocker "Network/DNS/TLS egress to the existing Cloud Run endpoint failed."
    add_action "Check the Claude Code cloud environment network policy and allow the existing Cloud Run hostname if required. Do not redeploy Cloud Run based only on this result."
    rm -f "$body"
    return 1
  fi

  add_observed "$name returned HTTP $code."
  case "$code" in
    2??)
      if [[ "$name" == "/readyz" ]]; then
        if ! python3 - "$body" <<'PY' >/dev/null 2>&1
import json, sys
with open(sys.argv[1], encoding='utf-8') as fh:
    data = json.load(fh)
raise SystemExit(0 if data.get('ready') is True else 1)
PY
        then
          add_blocker "Cloud Run answered /readyz but did not report ready=true."
          add_action "Inspect the existing service readiness, attached service account, Vertex AI/GCS configuration, and logs; do not create new infrastructure."
          rm -f "$body"
          return 1
        fi
        add_observed "/readyz reports ready=true."
      fi
      ;;
    401|403)
      add_blocker "Cloud Run or the application rejected the health/readiness probe."
      add_action "Check the existing ingress/IAM design before changing application credentials."
      rm -f "$body"
      return 1
      ;;
    421)
      add_blocker "The MCP application rejected the request host."
      add_action "Verify GOOGLE_MEDIA_MCP_ALLOWED_HOSTS includes the current run.app hostname."
      rm -f "$body"
      return 1
      ;;
    404)
      add_blocker "The hostname answered but the expected health/readiness route was not found."
      add_action "Verify the deployed revision and existing route paths; do not create a replacement service."
      rm -f "$body"
      return 1
      ;;
    503)
      add_blocker "Cloud Run is reachable but the service is not ready."
      add_action "Inspect existing Cloud Run readiness and server-side Google Cloud configuration."
      rm -f "$body"
      return 1
      ;;
    *)
      add_blocker "Cloud Run returned an unexpected HTTP status."
      add_action "Inspect existing Cloud Run request/application logs before changing configuration."
      rm -f "$body"
      return 1
      ;;
  esac
  rm -f "$body"
}

probe /healthz "$BASE_URL/healthz"
probe /readyz "$BASE_URL/readyz"

if [[ ${#BLOCKERS[@]} -gt 0 ]]; then
  report_failure
  exit 1
fi

printf 'OBSERVED\n'
printf -- '- %s\n' "${OBSERVED[@]}"
printf 'RESULT\n'
printf -- '- Google Media MCP preflight passed for project_slug=%s.\n' "$PROJECT_SLUG"
printf 'NEXT\n'
printf -- '- In Claude Code, confirm google-media in the native MCP server list, confirm generate_image/generate_video tools, run one minimal generate_image call first, and only after success run one minimal generate_video call.\n'
