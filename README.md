# claude-stack

A production Claude Code configuration: version-pinned MCP servers, smoke-tested, with anti-picks and known failure modes documented.

**The why and philosophy:** [shuman.de/stack](https://shuman.de/stack)
**This repo:** the actionable truth — clone, configure, run.

[![smoke-test](https://github.com/shumande/claude-stack/actions/workflows/smoke-test.yml/badge.svg)](https://github.com/shumande/claude-stack/actions/workflows/smoke-test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Install (90 seconds)

```bash
git clone https://github.com/shumande/claude-stack.git
cd claude-stack
bash scripts/install.sh
# Fill in tokens in .env (see comments)
bash scripts/smoke-test.sh
```

If smoke-test is green, you have a working baseline. Start Claude Code in this directory.

## What's in here

- `.mcp.json` — 7 verified MCP servers, version-pinned. Vercel MCP pending official package.
- `settings.example.json` — Claude Code settings with my `permissions.deny` baseline. Five hard-stop rules: no deletion outside project, no `.env` exfiltration, no `curl | sh` style outbound execution, no system-directory access, no credential-file reads.
- `CLAUDE.md` — my seven advisory rules at session start: commit hygiene, deploy discipline, secret handling, rate-limiting, PII masking, `/security-review` after each change.
- `scripts/smoke-test.sh` — Verifies each MCP server actually responds to `initialize`. Catches "fake-green" (process running but unresponsive).
- `scripts/install.sh` — Idempotent OS-aware setup. Detects macOS / Linux / WSL.
- `docs/anti-picks.md` — Tools I tried and dropped, with reasons.
- `docs/failure-modes.md` — Real ways this stack breaks, with fixes.
- `docs/gdpr-data-flows.md` — Where data lives for each tool. EU compliance helper.
- `docs/security-notes.md` — How the two-layer defense works.

## Plugins

This repo is also a plugin marketplace. The plugins are the European edition of
Anthropic's [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)
idea — German-market workflows, not translations.

- **`dsgvo`** — German data-protection compliance for websites: scan a site,
  review your Datenschutzerklärung, check cookie consent against DSGVO / BDSG /
  TDDDG. Every legal citation is pulled live from the
  [dsgvo.pro](https://dsgvo.pro) MCP, so paragraphs are real, not invented.
  See [`plugins/dsgvo/`](plugins/dsgvo/).

```bash
claude plugin marketplace add shumande/claude-stack
claude plugin install dsgvo@claude-stack
```

## What this is not

A tutorial. Read `docs/anti-picks.md` if you want the philosophy. Read [shuman.de/stack](https://shuman.de/stack) if you want the why.

## Maintenance

Monthly dependency review on the 1st of each month. Reviews logged in `CHANGELOG.md` with dates. CI runs smoke-test on every push and weekly.

If you see the last CHANGELOG entry is older than 60 days — assume this is abandoned and don't use it.

## License

MIT. Use it, fork it, ship better than I do.

## Author

[Oleksiy Shuman](https://shuman.de) — AI- & Automation-Architekt, Frankfurt.
