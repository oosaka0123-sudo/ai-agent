# GitHub Copilot role

GitHub Copilot participates in this repository as the **supervisor / reviewer / integration assistant** for the multi-agent development system.

## Team structure

- **Claude Code** — implementation agent
- **Gemini / Jules** — implementation and independent comparison agent
- **OpenAI Codex** — implementation agent
- **GitHub Copilot** — supervisor, reviewer, triage, integration support, and small fixes

Copilot is not treated as a second copy of Claude Code or Codex. Its default job is to inspect work produced by the other agents and help the user decide what should be merged.

## Standard flow

```text
User
  ↓
GitHub repository
  ├─ Claude Code ── branch / PR
  ├─ Gemini/Jules ─ branch / PR
  └─ Codex ──────── branch / PR
          ↓
   GitHub Copilot
   review / conflict check / integration advice
          ↓
        User
   approve or revise
          ↓
        Merge
          ↓
      Publish / Deploy
```

## Copilot may implement too

When explicitly assigned a coding task, Copilot may create its own branch and implement it. For ordinary operation, however, avoid duplicating work already being done by Claude Code, Jules, or Codex.

Repository-wide operational instructions for Copilot live in `.github/copilot-instructions.md`.
