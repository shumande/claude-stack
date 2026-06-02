---
name: website-scan
description: Scan a German-facing website for data-protection violations and turn the findings into a prioritized, plain-language fix list. Use when someone asks to check, scan, or audit a site for DSGVO/GDPR compliance, when preparing a site for launch, or when assessing Abmahnung (cease-and-desist) risk. Runs a live scan via the dsgvo.pro MCP and cites every finding to the exact paragraph.
argument-hint: "<website URL>"
---

# Website Scan (DSGVO)

> Connector setup and the API-key question are covered in [CONNECTORS.md](../../CONNECTORS.md).
> This skill needs the `check-compliance` tool, which requires an API key. The
> review skills (`datenschutz-review`, `cookie-consent`) work without one.

Run a real compliance scan of a website and translate the raw findings into a
report a non-lawyer business owner can act on. The point is not to dump the
scanner output — it is to prioritize, explain, and ground each issue in the
actual law.

## Trigger

User asks to "scan / check / audit [URL] for DSGVO", "prüfe [Website] auf
Datenschutz", "is my site GDPR-compliant", or "what's my Abmahnung risk".

## Inputs

1. **URL** — the page to scan. If the user gives a bare domain, scan the
   homepage and ask whether they also want a specific sub-page (the scanner
   sees the page it is given, so the imprint, privacy and cookie pages may need
   separate scans).
2. **Context (optional but useful)** — what the site is (shop, booking, lead
   form, brochure), whether it serves EU/German users, and what tools are
   embedded (analytics, fonts, maps, chat). This sharpens the interpretation.

## Process

### 1. Run the scan

Call the dsgvo.pro MCP `check-compliance` tool with the URL.

- If it returns `-32001` (no API key), stop and tell the user plainly: scans
  need a `dsp_live_` key (free tier 3/month), point them to
  https://dsgvo.pro/api-keys and [CONNECTORS.md](../../CONNECTORS.md). Offer to
  run `datenschutz-review` / `cookie-consent` instead, which need no key.
- Otherwise capture the `scanId`. Poll `get-scan-status` until done, then read
  `get-scan-result`.

### 2. Ground every finding

For each violation the scanner reports, fetch the cited article with
`get-article` (or `search-law` if you need to locate it). **Never state a
paragraph number from memory** — if the scan references e.g. §25 TDDDG or
Art. 13 DSGVO, pull the real text and quote the relevant sentence. This is the
whole reason the plugin exists; a wrong paragraph is worse than no paragraph.

### 3. Prioritize

Sort findings by real-world risk, not scanner order:

- **Critical** — actively triggers liability or Abmahnung risk today: tracking
  / non-essential cookies set before consent (§25 TDDDG), US-tool data transfer
  without basis, missing or unlawful consent banner, third-party requests
  (Google Fonts, Maps, YouTube) firing on load without consent.
- **High** — missing or incomplete mandatory pages: no Datenschutzerklärung, no
  Impressum, missing Art. 13 disclosures.
- **Medium** — present but incomplete (e.g. retention periods or recipients
  missing from the privacy policy).
- **Low** — hygiene and best practice.

### 4. Explain the fix

For each finding give a concrete, doable fix in business language — what to
change, not just what is wrong. Where the fix is a website change, be specific
("move the Matomo snippet behind a consent gate", "self-host the font instead
of loading fonts.googleapis.com").

## Output (in German)

The report is for a German business owner and possibly their lawyer — write it
in German.

```
# DSGVO-Scan: <URL>
Gescannt am <Datum> · <n> Befunde

## Zusammenfassung
<2–3 Sätze: Gesamtbild + größtes Risiko>

## Kritisch
| Befund | Rechtsgrundlage | Risiko | Was tun |
|--------|-----------------|--------|---------|
| ... | §25 TDDDG (Zitat) | Abmahnung | ... |

## Hoch / Mittel / Niedrig
<gleiche Tabelle je Stufe>

## Nächste Schritte
<priorisierte, nummerierte To-do-Liste>
```

Each "Rechtsgrundlage" cell must quote text actually returned by `get-article`.

## After

Offer to: run `datenschutz-review` on the privacy page, run `cookie-consent` on
the banner, re-scan after fixes, or draft the missing pages.

## Boundaries

This is decision-support, not legal advice. State once, plainly, that the
output should be confirmed by a Datenschutzbeauftragter or lawyer before relying
on it — especially for transfers, consent design, and DSFA. Do not invent
case-law or Abmahnung statistics; if you don't have a figure from the scan or
the law, say so.
