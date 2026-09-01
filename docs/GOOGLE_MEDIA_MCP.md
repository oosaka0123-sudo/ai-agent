# Google Media MCP — Architecture, Setup, Troubleshooting

Shared Google Vertex AI (Imagen / Veo) media generation, exposed to every
Claude Code project as MCP tools, without any project re-implementing
generation itself or holding Google Cloud credentials.

## Architecture

```
Claude Code (any registered project)
        │  reads .mcp.json → mcpServers.google-media
        ▼
Remote HTTP MCP  (mcp_server/, this repository)
        │  generate_image / generate_video
        │  runs job → poll → success/failed → upload, entirely server-side
        ▼
Google Cloud Run  (project: rss7-ai-media)
        │  Application Default Credentials (attached service account)
        ▼
Google Vertex AI
        ├─ Imagen  (images)
        └─ Veo     (video)
                │
                ▼
        Google Cloud Storage
        projects/{project_slug}/images/YYYY/MM/...
        projects/{project_slug}/videos/YYYY/MM/...
```

Nothing in this chain reuses a different implementation for the same job:
`mcp_server/` wraps `src/media_gen/` (the Vertex AI backend from PR #26)
rather than reimplementing it, and `scripts/onboard_projects.py` (PR #25)
is what distributes `.mcp.json` to every registered project rather than a
second distribution mechanism.

### Why video generation never makes Claude Code poll

`generate_video` starts the Veo job, polls `operations.get` on an interval,
and only returns once the job succeeds, fails, or times out
(`GOOGLE_MEDIA_VIDEO_TIMEOUT_SECONDS`, default 600s) — all inside the one
MCP tool call. Claude Code makes a single call and gets a final result; it
never receives a job ID to poll separately.

### Provider routing (Google today, Higgsfield planned)

`mcp_server/provider_router.py` resolves `provider="google"` /
`"auto"` (→ google, the only implemented provider right now) /
`"higgsfield"` (a named, not-yet-implemented error, not a 404). Adding
Higgsfield later means adding one provider module with the same
`generate_image` / `generate_video` contract as
`media_gen/providers/google_provider.py` and registering its name in
`provider_router.py` — nothing else in this package references provider
names directly.

## New-site addition (should require no new Google Cloud work)

1. Run **Register Site** (`.github/workflows/register-site.yml`, or
   `scripts/register_project.py` directly) with the new site's slug,
   name, and repository. This opens a PR against `projects/registry.json`
   in this repository.
2. Once merged, **Auto Site Onboarding**
   (`.github/workflows/auto-site-onboarding.yml`) opens a PR in the target
   repository adding:
   - `.ai-agent/project.json`, `.ai-agent/README.md` — always.
   - `.mcp.json`'s `mcpServers.google-media` entry — only once
     `projects/registry.json`'s `onboarding.google_media_mcp_url` is set
     (see "Google Cloud initial setup" below) *and* the project's
     `media.enabled` is `true`. This is a **merge**, not a file
     replacement: any other MCP servers already configured in that
     repository's `.mcp.json` are left untouched.
3. Once that PR is merged and the project sets
   `GOOGLE_MEDIA_MCP_TOKEN` wherever its Claude Code sessions run (see
   below), `generate_image` / `generate_video` are available there.

Steps 1–3 repeat identically for the 10th or 20th site — no new Google
Cloud configuration is needed per site.

## Google Cloud initial setup (human, one time)

Everything below is a one-time setup for the *shared* MCP server, not
per-project.

1. **Enable APIs** (project `rss7-ai-media`):
   ```
   gcloud services enable aiplatform.googleapis.com storage.googleapis.com run.googleapis.com --project=rss7-ai-media
   ```
2. **Create the GCS bucket** for generated media:
   ```
   gcloud storage buckets create gs://rss7-ai-media-genmedia --project=rss7-ai-media --location=us-central1 --uniform-bucket-level-access
   ```
3. **Create a Cloud Run service account** with the minimum IAM it needs —
   not Owner/Editor:
   ```
   gcloud iam service-accounts create google-media-mcp --project=rss7-ai-media --display-name="Google Media MCP (Cloud Run)"

   gcloud projects add-iam-policy-binding rss7-ai-media \
     --member="serviceAccount:google-media-mcp@rss7-ai-media.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

   gcloud storage buckets add-iam-policy-binding gs://rss7-ai-media-genmedia \
     --member="serviceAccount:google-media-mcp@rss7-ai-media.iam.gserviceaccount.com" \
     --role="roles/storage.objectAdmin"
   ```
4. **Generate an inbound token** (protects the MCP endpoint itself — Vertex
   AI calls cost money, so this must not be publicly callable without one):
   ```
   openssl rand -hex 32
   ```
5. **Deploy to Cloud Run**, attaching the service account from step 3 (no
   service-account JSON key — this is what makes ADC work) and the env
   vars from `.env.example`'s "Google Media MCP Server" section:
   ```
   gcloud run deploy google-media-mcp \
     --project=rss7-ai-media --region=us-central1 \
     --source=. \
     --service-account=google-media-mcp@rss7-ai-media.iam.gserviceaccount.com \
     --no-allow-unauthenticated \
     --set-env-vars=GOOGLE_CLOUD_PROJECT=rss7-ai-media,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_MEDIA_GCS_BUCKET=rss7-ai-media-genmedia \
     --set-secrets=GOOGLE_MEDIA_MCP_TOKEN=google-media-mcp-token:latest
   ```
   `--no-allow-unauthenticated` adds Cloud Run's *own* IAM-based auth in
   front of the app's bearer-token check — defense in depth, not a
   replacement for it. If callers won't have Google identities (Claude
   Code sessions generally won't), use `--allow-unauthenticated` instead
   and rely on `GOOGLE_MEDIA_MCP_TOKEN` alone; either way the token is
   required.
6. **Set the allowed host** — the MCP SDK's DNS-rebinding protection
   defaults to an empty allow-list, which rejects *every* request,
   including legitimate ones, until this is set to the deployed hostname:
   ```
   gcloud run services update google-media-mcp --region=us-central1 \
     --update-env-vars=GOOGLE_MEDIA_MCP_ALLOWED_HOSTS=<service-url-host>
   ```
7. **Record the URL** in `projects/registry.json`:
   `onboarding.google_media_mcp_url` = `https://<service-url>/mcp`. This
   is what turns on `.mcp.json` distribution for every registered project
   (step 2 above).
8. **Share `GOOGLE_MEDIA_MCP_TOKEN`** with whoever needs to set it in a
   registered project's Claude Code environment (not committed to any
   repository — see "MCP URL / token setup" below).

None of this repeats per project. Steps 1–3 are per Google Cloud project
(`rss7-ai-media`), and steps 4–7 are per MCP server deployment.

## MCP URL / token setup (per project, one time)

`.mcp.json`'s `google-media` entry (see
`scripts/onboard_projects.py::merge_mcp_json`) is:

```json
{
  "mcpServers": {
    "google-media": {
      "type": "http",
      "url": "${GOOGLE_MEDIA_MCP_URL:-https://<the deployed service URL>/mcp}",
      "headers": { "Authorization": "Bearer ${GOOGLE_MEDIA_MCP_TOKEN}" }
    }
  }
}
```

The URL already has the real Cloud Run URL baked in as the default, so
nothing extra is needed for the endpoint to resolve. `GOOGLE_MEDIA_MCP_TOKEN`
is deliberately **not** filled in or committed anywhere — set it as an
environment variable wherever that project's Claude Code sessions run
(shell profile, CI secret, etc.). `GOOGLE_MEDIA_MCP_URL` is also available
as an override if a project ever needs to point at a different deployment
(e.g. staging).

## Service Account / IAM summary

| Identity | Role | Scope | Why |
|---|---|---|---|
| Cloud Run service account (`google-media-mcp@...`) | `roles/aiplatform.user` | project `rss7-ai-media` | Call Imagen/Veo — nothing broader (no Editor/Owner). |
| Cloud Run service account | `roles/storage.objectAdmin` | bucket `rss7-ai-media-genmedia` only | Write generated media — not project-wide storage access. |
| `CONTROL_PLANE_GITHUB_TOKEN` (GitHub secret, this repo) | fine-grained: target repo `Contents: RW`, `Pull requests: RW`, `Metadata: R` | only repos actually onboarded | Open onboarding PRs — never used for Google Cloud. |
| `GOOGLE_MEDIA_MCP_TOKEN` | N/A (application-level bearer secret) | the MCP endpoint only | Not a Google Cloud credential; just gates who can trigger billed generation calls. |

## Troubleshooting

**Authentication error calling Vertex AI** (`authentication` category in
audit logs / tool error) — `/readyz` returning 503 with a
`GOOGLE_CLOUD_PROJECT is not set` (or similar) message means the *server's*
config is incomplete; a 401/`Could not find default credentials` from
Vertex AI itself means the Cloud Run service account isn't attached
correctly (re-check the `--service-account` flag in the deploy step) —
this only affects the server, not each project, since there's one shared
identity.

**Quota exceeded** (`quota_exceeded`) — Vertex AI per-project quota for
Imagen/Veo. Request a quota increase in the `rss7-ai-media` Google Cloud
console; this is not something any per-project config can work around.

**Billing** (`billing`) — billing account not linked, or disabled, on
`rss7-ai-media`. Check the Google Cloud console's Billing page for that
project.

**Veo / Imagen unavailable** (`model_unavailable`) — either the specific
model ID is wrong/retired (Vertex AI model names change over time; check
current model IDs before assuming an outage) or the model isn't available
in `GOOGLE_CLOUD_LOCATION`. Vertex AI generative video/image models are
region-restricted; `us-central1` is the default here specifically because
it has broad availability, but confirm before changing it.

**MCP connection error from Claude Code** — check, in order: (1) is
`GOOGLE_MEDIA_MCP_TOKEN` actually set in the environment Claude Code is
running in (a missing token means every call gets a 401 before it reaches
any tool); (2) is `.mcp.json` present and does its `url` resolve to a live
service (`curl https://.../healthz` should return `ok`); (3) does
`/readyz` return `{"ready": true}` — if not, the server's own GCP env vars
are the problem, not the client; (4) `GOOGLE_MEDIA_MCP_ALLOWED_HOSTS` not
including the real hostname causes a `421 Invalid Host header` for every
request, including correctly authenticated ones — this is easy to
mistake for an auth problem since it also returns a 4xx.

**Rate limited within this server** (`rate_limited`, or a
`invalid_request` error naming `count`/`duration_seconds` exceeding a
cap) — these are `mcp_server`'s own cost-safety limits
(`GOOGLE_MEDIA_MAX_*` env vars / the global concurrency cap, which falls
back to `projects/registry.json`'s `max_parallel_projects` if unset), not
a Vertex AI error. Adjust the relevant env var if the cap is genuinely too
low for legitimate use — don't raise it reflexively.
