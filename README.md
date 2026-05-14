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
- `settings.example.json` — Claude Code settings with `permissions.deny` baseline (Miller §A — 5 enforced safety rules).
- `CLAUDE.md` — 7 advisory safety rules (Miller §B).
- `scripts/smoke-test.sh` — Verifies each MCP server actually responds to `initialize`. Catches "fake-green" (process running but unresponsive).
- `scripts/install.sh` — Idempotent OS-aware setup. Detects macOS / Linux / WSL.
- `docs/anti-picks.md` — Tools I tried and dropped, with reasons.
- `docs/failure-modes.md` — Real ways this stack breaks, with fixes.
- `docs/gdpr-data-flows.md` — Where data lives for each tool. EU compliance helper.
- `docs/security-notes.md` — How the two-layer defense works.

## What this is not

A tutorial. Read `docs/anti-picks.md` if you want the philosophy. Read [shuman.de/stack](https://shuman.de/stack) if you want the why.

## Maintenance

Monthly dependency review on the 1st of each month. Reviews logged in `CHANGELOG.md` with dates. CI runs smoke-test on every push and weekly.

If you see the last CHANGELOG entry is older than 60 days — assume this is abandoned and don't use it.

## License

MIT. Use it, fork it, ship better than I do.

## Author

[Oleksiy Shuman](https://shuman.de) — AI- & Automation-Architekt, Frankfurt.
