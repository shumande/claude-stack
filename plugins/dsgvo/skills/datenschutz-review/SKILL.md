---
name: datenschutz-review
description: Review or draft a German privacy policy (Datenschutzerklärung) against the mandatory disclosures of Art. 13/14 DSGVO, flagging gaps by severity with concrete German wording fixes. Use when someone shares a Datenschutzerklärung to check, asks whether their privacy policy is complete, or needs one drafted. Every requirement is grounded in the live article text via the dsgvo.pro MCP. Works without an API key.
argument-hint: "<privacy policy text or URL>"
---

# Datenschutzerklärung Review

> Connectors and tools: [CONNECTORS.md](../../CONNECTORS.md). This skill uses
> only the free `get-article` / `search-law` tools — no API key needed.

Check a German privacy policy against what the DSGVO actually requires, or draft
one. The value is grounding: pull the real Art. 13/14 (and related) text and
check the document against it, clause by clause — instead of working from a
remembered checklist that drifts out of date.

## Trigger

User shares a Datenschutzerklärung / privacy policy (pasted or as a URL), or
asks to "review / check / prüfe my Datenschutzerklärung", "is my privacy policy
complete", or "draft a Datenschutzerklärung".

## Inputs

1. **The policy** — pasted text, or a URL (fetch it). If drafting from scratch,
   gather: who the controller is (name, address, contact), what data is
   processed and why, which tools/recipients (analytics, hosting, payment,
   newsletter, fonts/maps), whether data leaves the EU, and whether there is a
   DPO (Datenschutzbeauftragter).
2. **Site context** — what the site does, so processing purposes and legal
   bases can be assessed for plausibility.

## Grounding step (do this first)

Fetch the requirement text before judging the document:

- `get-article` for **Art. 13 DSGVO** (data collected from the person) and
  **Art. 14 DSGVO** (data from third parties) — the mandatory-information lists.
- As needed: **Art. 6** (legal basis), **Art. 28** (processors / AVV),
  **Art. 15–22** (data-subject rights), **Art. 44 ff.** (third-country
  transfers), and **§ 5 DDG** for the Impressum link.
- Use `search-law` when you need to locate the right provision.

Build the checklist from the returned text, not from memory.

## Review dimensions

Check the document for each mandatory disclosure and mark present / incomplete /
missing:

- **Controller identity & contact** (Art. 13(1)(a))
- **DPO contact**, if one is required/appointed (Art. 13(1)(b))
- **Purposes and legal basis** for each processing (Art. 13(1)(c), Art. 6) —
  and whether the stated basis is plausible (e.g. consent vs. legitimate
  interest for analytics)
- **Legitimate interests**, where that is the basis (Art. 13(1)(d))
- **Recipients / categories of recipients** (Art. 13(1)(e)) — named tools
- **Third-country transfers** and the safeguard relied on (Art. 13(1)(f),
  Art. 44 ff.)
- **Retention periods** or the criteria for them (Art. 13(2)(a))
- **Data-subject rights**: access, rectification, erasure, restriction,
  portability, objection (Art. 13(2)(b), Art. 15–22)
- **Right to withdraw consent** where consent is used (Art. 13(2)(c))
- **Right to lodge a complaint** with a supervisory authority (Art. 13(2)(d))
- **Whether provision of data is required** and the consequences (Art. 13(2)(e))
- **Automated decision-making / profiling**, if any (Art. 13(2)(f))
- **Tool-specific clauses** present for each embedded service actually used

## Output (in German)

```
# Datenschutzerklärung – Prüfbericht

## Zusammenfassung
<Gesamtbild + die wichtigsten Lücken in 2–3 Sätzen>

## Lückenanalyse
| Pflichtangabe | Status | Rechtsgrundlage | Befund / Fix |
|---------------|--------|-----------------|--------------|
| Verantwortlicher | vorhanden | Art. 13(1)(a) DSGVO (Zitat) | ... |
| Aufbewahrungsfristen | fehlt | Art. 13(2)(a) DSGVO (Zitat) | Ergänzen: ... |

## Vorher / Nachher
<für die wichtigsten Lücken: Originaltext → Vorschlag auf Deutsch>
```

"Rechtsgrundlage" cells must quote text returned by `get-article`. If a clause
is missing, supply ready-to-paste German wording.

## Drafting mode

If asked to draft, produce a structured Datenschutzerklärung covering every
Art. 13 item above, with clearly marked `[Platzhalter]` for facts you don't have
(addresses, specific tools, retention periods). Do not fabricate the controller
details or invent which tools are in use.

## After

Offer to: draft the missing clauses, run `cookie-consent` on the consent banner,
or run `website-scan` to verify what actually loads on the page.

## Boundaries

Decision-support, not legal advice — say so once. Flag, don't resolve, genuinely
legal judgment calls (e.g. whether legitimate interest holds, whether a DSFA is
required); recommend a Datenschutzbeauftragter or lawyer for those.
