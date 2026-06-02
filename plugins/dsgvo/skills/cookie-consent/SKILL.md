---
name: cookie-consent
description: Check a website's cookie banner and consent flow against § 25 TDDDG (and the PIMS rule in § 26), flagging dark patterns and missing consent with concrete German fixes. Use when someone asks to review a cookie banner, consent manager, or whether their cookies are lawful before non-essential scripts load. Grounds every rule in the live paragraph via the dsgvo.pro MCP. Works without an API key.
argument-hint: "<banner description or URL>"
---

# Cookie Consent Check (§ 25 TDDDG)

> Connectors and tools: [CONNECTORS.md](../../CONNECTORS.md). Uses the free
> `get-article` / `search-law` tools — no API key needed.

Assess whether a site stores or reads information on the user's device lawfully.
In Germany the controlling rule is **§ 25 TDDDG**, not the DSGVO directly:
non-essential cookies and similar technologies require **prior, informed,
voluntary consent**. This skill checks the banner and flow against that rule and
the common dark-pattern failures regulators act on.

## Trigger

User asks to "check / review my cookie banner / consent / Cookie-Banner
prüfen", "are my cookies DSGVO/TDDDG compliant", or "is my consent manager OK".

## Inputs

1. **The banner / flow** — a URL (inspect what loads and the banner behavior),
   a screenshot/description, or the consent-tool config. If given a URL,
   consider running `website-scan` to see which scripts actually fire on load
   (that needs an API key; the consent-design checks below do not).
2. **What's embedded** — analytics, ads, maps, fonts, video, chat — anything
   non-essential, since those are what consent must gate.

## Grounding step (do this first)

- `get-article` for **§ 25 TDDDG** (consent for storing/accessing information on
  terminal equipment, and the narrow "strictly necessary" exception).
- `get-article` for **§ 26 TDDDG** (recognized consent-management / PIMS), if
  the user uses or asks about a consent service.
- Cross-reference **Art. 4(11)** and **Art. 7 DSGVO** for what valid consent
  requires (freely given, specific, informed, unambiguous; as easy to withdraw
  as to give).

Quote the returned text — do not state the paragraph from memory.

## Checklist

- **Prior consent** — non-essential cookies/scripts must NOT fire before the
  user opts in. (Most common, highest-risk failure.)
- **Strictly-necessary exception** — only genuinely essential cookies may run
  without consent; "we need analytics" does not qualify.
- **Granularity** — consent per purpose/category, not one all-or-nothing toggle.
- **No pre-ticked boxes** — defaults must be off (Planet49 / Art. 4(11)).
- **Reject as easy as accept** — an "Accept all" with no equally prominent
  "Reject all" on the first layer is a dark pattern.
- **No nudging** — no colour/size tricks steering to accept, no "legitimate
  interest" pre-enabled for tracking, no cookie wall where avoidable.
- **Informed** — purposes, recipients, durations, and a link to the
  Datenschutzerklärung reachable from the banner.
- **Withdrawable** — a persistent way to change/withdraw consent later
  (Art. 7(3)); withdrawal as easy as giving.
- **Documented** — consent is logged (who, when, what version).

## Output (in German)

```
# Cookie-Consent-Prüfung: <URL/Banner>

## Gesamturteil
<konform / Mängel / kritisch — in 1–2 Sätzen>

## Befunde
| Anforderung | Status | Rechtsgrundlage | Fix |
|-------------|--------|-----------------|-----|
| Vorab-Einwilligung | verletzt | § 25 TDDDG (Zitat) | Skripte hinter Consent-Gate ... |
| Ablehnen so einfach wie Zustimmen | verletzt | Art. 7 DSGVO (Zitat) | "Alle ablehnen" gleichwertig auf Ebene 1 ... |

## Empfehlung
<priorisierte Schritte; ggf. Hinweis auf § 26 TDDDG-anerkannten Dienst>
```

"Rechtsgrundlage" cells must quote `get-article` output.

## After

Offer to: run `website-scan` to confirm what loads before consent, or
`datenschutz-review` to check the linked privacy policy matches the banner.

## Boundaries

Decision-support, not legal advice — say so once. Consent design and the
"strictly necessary" line can be genuinely contested; flag close calls and
recommend a Datenschutzbeauftragter rather than asserting certainty.
