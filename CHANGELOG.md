# Changelog

All notable changes documented here. Monthly dependency reviews logged with date.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- This repo is now also a plugin marketplace (`.claude-plugin/marketplace.json`).
- `dsgvo` plugin (`plugins/dsgvo/`) — German digital-law compliance for websites. European edition of Anthropic's knowledge-work-plugins idea. Skills are grounded in real law via the dsgvo.pro MCP (`get-article`/`search-law`), so paragraph citations are live, not recalled.
  - v0.1.0 — `website-scan`, `datenschutz-review`, `cookie-consent` (DSGVO / TDDDG).
  - v0.2.0 — added `impressum` (§ 5 DDG) and `ki-vo-classify` (AI Act risk tiers, Art. 5 / 6 / 50 KI-VO).
- Initial repo: 7 verified MCP servers (Context7, Supabase, Higgsfield, atypica, Gamma, DSGVO.pro, Notion). Vercel MCP not yet available as official package — noted in `_unverified` section of `.mcp.json`.
- Smoke-test script (`scripts/smoke-test.sh`) with portable `timeout` handling and SIGPIPE-safe stdio test.
- Idempotent install script (`scripts/install.sh`) with OS detection.
- CI workflow: `smoke-test` runs on every push + weekly Monday cron.
- Documentation: security notes, anti-picks, failure modes, GDPR data flows.
- My `permissions.deny` baseline in `settings.example.json` (5 hard-stop rules).
- My 7 safety guards in `CLAUDE.md` (commit hygiene, deploy discipline, secret handling, etc.).

## [0.1.0] — 2026-MM-DD

First public release. See README for context.
