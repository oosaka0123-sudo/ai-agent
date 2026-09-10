# Mobile navigation stacking follow-up

Claude Code review of the #70 fix found that the root-level `.nav-backdrop` used `z-index: 64`, while `.topbar` created a stacking context at `z-index: 60`. As a result, the backdrop could paint above the entire topbar subtree and visually hide the open drawer and hamburger button at mobile widths.

The fix lowers the backdrop to `z-index: 55`, keeping it below the topbar context while still dimming page content. The existing deterministic `display:none` / `display:flex` open state, Escape close, backdrop close, link close and focus return remain unchanged.

The same review confirmed that ordinary pages no longer contain video elements; generated videos remain only in MEDIA LAB with controls and explanatory labels.
