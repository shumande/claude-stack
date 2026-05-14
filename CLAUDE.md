# CLAUDE.md — Project Guidance for Claude Code

This is a reference Claude Code stack: version-pinned MCP servers, smoke-tested in CI, with anti-picks and known failure modes documented.

## Safety Rules (7 Guards, derived from Миллер / Smyslokod Method)

When working in this codebase, Claude Code MUST follow these guardrails:

1. **Commit only your changes.** Never commit unrelated files.
2. **Never deploy without an explicit "deploy" command.** No auto-deploy.
3. **Control the deploy process end-to-end.** If a deploy fails, fix and retry — don't leave broken state.
4. **Never store passwords or API keys in code.** Only in `.env` (which is in `.gitignore`).
5. **Set rate limits on endpoints** if you add any (this repo has none currently, but the rule applies if extended).
6. **Encrypt user PII.** Mask in logs (phone → `+38050***1234`, email → `a***@gmail.com`).
7. **Run `/security-review` after each major code change.**

## Layer separation

- `settings.example.json` `permissions.deny` block — what Claude is **never allowed to do** (enforced).
- These 7 rules in CLAUDE.md — what Claude must **remember while working** (advisory).

Both layers run together. See `docs/security-notes.md`.

## What this repo is

A reference production stack: Claude Code + a curated set of MCP servers, version-pinned. The pages on `shuman.de/stack` explain the philosophy and categories. This repo is the actionable truth: clone, configure `.env`, run `bash scripts/smoke-test.sh`, get a working baseline.

## What this repo is not

- A tutorial. Read `docs/anti-picks.md` for tools dropped and why.
- A "complete" list. Read `docs/failure-modes.md` for the parts that break.
- A production system. It's a baseline. Adapt to your workflow.
