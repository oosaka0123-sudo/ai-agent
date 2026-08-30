---
name: code-review
description: Review pull requests for this multi-agent, smartphone-centered GitHub development system. Check specification compliance, AI-branch safety, mobile UX, security, regressions, deployment risk, and whether a human decision is required.
---

# Code Review Skill

Use this skill whenever reviewing a pull request in this repository.

## Read first

Before forming a conclusion, inspect and follow the applicable repository instructions, especially:

1. `AGENTS.md`
2. `.github/copilot-instructions.md`
3. `PROJECT_SPEC.md`
4. `docs/DEVELOPMENT.md`
5. Agent-specific instructions relevant to the PR (`CLAUDE.md`, `GEMINI.md`, `CODEX.md`, `COPILOT.md`)

Do not approve a PR from its title or description alone. Review the actual changed files.

## Required checks

### 1. Task and specification
- Confirm the implementation actually matches the stated task.
- Flag unrelated changes or scope creep.
- Preserve existing behavior unless the task explicitly changes it.

### 2. Multi-agent branch safety
- Identify which agent or workflow produced the PR when possible.
- Check whether the change overlaps another active PR or parallel branch.
- Flag likely conflicts, duplicated work, or stale-base risks.
- Never recommend direct pushes to `main`.

### 3. Security and privacy
- Look for secrets, API keys, tokens, credentials, private data, unsafe permissions, injection risks, XSS, insecure network calls, or dangerous workflow permissions.
- Treat changes under `.github/workflows/` as security-sensitive.
- For `pull_request_target`, verify that untrusted PR code is not checked out or executed with privileged permissions.

### 4. Web and PWA quality
For web/PWA changes, check at minimum:
- Mobile usability around 390px viewport width.
- Broken layout, overflow, unreadable text, tap-target problems, and navigation regressions.
- Obvious JavaScript/runtime errors and broken links.
- PWA/service-worker/cache changes for stale-content or update risks.
- Performance regressions when large assets, blocking scripts, or repeated network calls are introduced.

### 5. Tests and verification
- Check whether realistic verification steps exist.
- Do not treat an unverified claim such as “tested successfully” as proof when the diff or CI contradicts it.
- If CI is available, consider its state in the recommendation.

### 6. Factual and time-sensitive content
For guides, pricing, product capabilities, limits, or other time-sensitive factual claims:
- Flag claims that appear undated, unsupported, internally inconsistent, or likely to become stale.
- Prefer explicit dates and primary-source verification for important current facts.
- Do not present factual freshness as a code-quality approval if it was not actually verified.

### 7. Deployment and merge risk
Classify whether the PR changes:
- documentation only,
- non-production code,
- production runtime code,
- deployment/workflow configuration,
- authentication/secrets/security-sensitive behavior.

Raise the review strictness as deployment risk increases.

## Review outcome

End with exactly one of these recommendations:

- `🟢 Approval recommended` — no blocking issue found.
- `🟡 Human decision required` — technically acceptable but product/content/architecture choice requires the user.
- `🔴 Changes required` — one or more concrete blocking issues must be fixed.

When issues exist, state:
1. what is wrong,
2. why it matters,
3. the smallest practical fix.

Prefer a small number of high-value findings over noisy style comments.

## Human control boundary

Copilot is the supervisor/reviewer, not the final owner.
- Do not auto-merge merely because review is green.
- Do not silently choose between competing agent implementations.
- Explicitly mark product-direction, publication, destructive, paid-plan, credential, or security decisions as human decisions.
