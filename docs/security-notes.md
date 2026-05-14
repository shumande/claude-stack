# Security notes

Two layers protect this stack — enforced and advisory. They don't conflict; they reinforce each other.

## Layer 1: `permissions.deny` (enforced)

The `settings.example.json` file ships with a `permissions.deny` block — Claude Code will refuse these commands at the harness level. This is **not advisory**; it's a hard stop.

Covered:
- Deletion outside project root (`rm -rf` patterns).
- Secrets leakage from `.env` (no `cat .env`, no `curl --data @.env`).
- Outbound data export (no `curl | sh`, no `export | curl`).
- System directory access (`/etc`, `/usr/local`, `/var`).
- Credential paths (`**/.aws/credentials`, `**/credentials.json`).

You can extend the deny list in your own `.claude/settings.local.json` — that file is gitignored.

## Layer 2: 7 guardrails in `CLAUDE.md` (advisory)

These are reminders Claude reads at the start of each session:

1. Commit only your changes.
2. No deploy without explicit "deploy" command.
3. Control deploy end-to-end.
4. No secrets in code — only `.env`.
5. Rate-limit endpoints.
6. Encrypt PII, mask in logs.
7. Run `/security-review` after each major change.

Source: Miller / Smyslokod method final formulation (PDF-CHK, 7 rules; the 7th is new vs the earlier 6).

## Why both?

- `permissions.deny` is non-bypassable but narrow — it can only check command shapes.
- `CLAUDE.md` rules are broader (PII masking, rate-limiting) but rely on Claude's discipline.

In combination they cover: "don't run this" + "remember this principle while running other things."

## Recovery / dangerous triad

This repo assumes you have `bypass permissions` + `Allow Mode` + `auto-commit` enabled — that combination ("опасная тройка") makes Claude fast but means `git` is your safety belt. The repo is on GitHub from day one for exactly this reason: any wrong turn → `git reset` is fine.
