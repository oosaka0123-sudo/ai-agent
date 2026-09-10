# Issue #72 self evaluation

- Root cause: root stacking context ordering between `.topbar` and `.nav-backdrop`.
- Fix scope: one runtime CSS z-index value only.
- Risk: low; no navigation behavior or link structure changed.
- Media check: non-MEDIA-LAB pages contain no videos after #71.
- Final gate: PR CI, merge, Pages deploy, live 390px verification.
