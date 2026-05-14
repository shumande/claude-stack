# Anti-picks

Tools I tried and dropped. The reason is more useful than the tool name.

> **Format per entry:** `### <tool name>` → `**Why dropped:** <category>` → 1-3 sentences explaining the specific failure mode I hit.
>
> **Categories:** zombie processes · token bloat · maintenance abandoned · pricing · silent failures · supersedence · platform mismatch

---

### Figma MCP

**Why dropped:** supersedence

Claude Design (Anthropic) replaces the design-to-code role in my workflow. Since adopting it I haven't reached for Figma MCP — the round-trip (brief → design → handoff → code) collapses into a single conversation. Figma MCP stays in the public ecosystem; it just isn't the right entry point for how I work.

---

### Notion MCP

**Why dropped:** supersedence

Obsidian is my Second Brain — local-first markdown that Claude Code reads natively without an MCP layer. The friction of cloud sync, page-graph model, and Notion's API limits never paid back. Markdown files in a vault beat database-as-notes for how I think.

---

### Slack MCP

**Why dropped:** platform mismatch

Solo operator, no team chat to integrate. Slack MCP solves a problem I don't have. Adding it would be cargo-cult of a stack shape that fits agencies, not single-operator workflows.

---

### Sentry

**Why dropped:** maintenance abandoned

Tried as error monitoring for production apps. The noise-to-signal stayed bad at solo-operator scale: most alerts I cared about were already visible in Vercel logs + Trigger.dev run history. Sentry became a dead actor — UI tab open, never checked, paying for it monthly. Pulled the plug.

---

<!-- Add 1+ more entries from your own experience as they accumulate. -->

