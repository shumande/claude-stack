# Changelog

All notable changes documented here. Monthly dependency reviews logged with date.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- This repo is now also a plugin marketplace (`.claude-plugin/marketplace.json`).
- `dsgvo` plugin (`plugins/dsgvo/`) — German data-protection compliance for websites: `website-scan`, `datenschutz-review`, `cookie-consent`. Skills are grounded in real law via the dsgvo.pro MCP (`get-article`/`search-law`), so paragraph citations are live, not recalled. European edition of Anthropic's knowledge-work-plugins idea.
- Initial repo: 7 verified MCP servers (Context7, Supabase, Higgsfield, atypica, Gamma, DSGVO.pro, Notion). Vercel MCP not yet available as official package — noted in `_unverified` section of `.mcp.json`.
- Smoke-test script (`scripts/smoke-test.sh`) with portable `timeout` handling and SIGPIPE-safe stdio test.
- Idempotent install script (`scripts/install.sh`) with OS detection.
- CI workflow: `smoke-test` runs on every push + weekly Monday cron.
- Documentation: security notes, anti-picks, failure modes, GDPR data flows.
- My `permissions.deny` baseline in `settings.example.json` (5 hard-stop rules).
- My 7 safety guards in `CLAUDE.md` (commit hygiene, deploy discipline, secret handling, etc.).

## [0.1.0] — 2026-MM-DD

First public release. See README for context.
