---
name: impressum
description: Check a website's Impressum (legal notice) against the mandatory information duties of § 5 DDG, flagging missing or misplaced items with concrete German fixes. Use when someone asks to check, review, or audit their Impressum, asks what their Impressum must contain, or is launching a site. Grounds the legal basis live via the dsgvo.pro MCP. Works without an API key.
argument-hint: "<Impressum text or URL>"
---

# Impressum Check (§ 5 DDG)

> Connectors and tools: [CONNECTORS.md](../../CONNECTORS.md). Uses the free
> `get-article` / `search-law` tools — no API key needed.

Check whether a site's Impressum meets the German Impressumspflicht. Since May
2024 the controlling rule is **§ 5 DDG** (Digitale-Dienste-Gesetz), which
replaced § 5 TMG. The duty applies to business / commercial digital services and
the information must be **easily recognizable, directly accessible, and
permanently available** (leicht erkennbar, unmittelbar erreichbar, ständig
verfügbar). A missing or buried Impressum is a common Abmahnung trigger.

## Trigger

User asks to "check / review / prüfe my Impressum", "what must my Impressum
contain", "is my legal notice complete", or is preparing a site for launch.

## Inputs

1. **The Impressum** — pasted text or a URL (fetch it; also note whether it's
   reachable in one click from every page, e.g. in the footer).
2. **The business** — legal form (Einzelunternehmen, GbR, GmbH, UG, …),
   whether it's a regulated profession (Arzt, Anwalt, Steuerberater, Makler,
   Handwerk …), whether VAT-registered, and whether it's in a register
   (Handelsregister, etc.). These drive which extra items are required.

## Grounding step (do this first)

- `get-article` for **§ 5 DDG** (Allgemeine Informationspflichten) — the
  controlling provision. Quote it as the legal basis.
- For regulated professions, also note **§ 5(1) Nr. … DDG** items on
  Kammer / Aufsichtsbehörde / berufsrechtliche Regelungen, and use `search-law`
  if a specific professional rule is in scope.
- Do not state the paragraph from memory — cite what the tool returns.

## § 5 DDG mandatory items

Check each (the catalog is settled law; the legal basis is § 5 DDG):

- **Name / company name** and **legal form** (e.g. "Mustermann GmbH")
- **Authorized representative** for legal persons (Geschäftsführer /
  Vertretungsberechtigter)
- **Full postal address** — a real street address, **not** just a P.O. box
- **Contact**: an email address **and** a second fast means (telephone or a
  contact form that gets a prompt reply)
- **Register and registration number**, if entered in one (Handelsregister,
  Vereinsregister, …) plus the Registergericht
- **VAT ID (USt-IdNr.)** per § 27a UStG, if one exists (or
  Wirtschafts-Identifikationsnummer)
- **Supervisory authority (Aufsichtsbehörde)**, where the activity needs
  authorization
- **Regulated-profession details**, if applicable: Kammer, the legal job title
  and the state that granted it, and where the professional rules are found
- **Acting journalistically?** Then a responsible person (V. i. S. d. P.) with
  address
- **EU ODR platform link** and a line on consumer-arbitration participation,
  where relevant

## Placement checks (not just content)

- Reachable from **every** page (typically a footer "Impressum" link)
- **One click**, plainly labeled "Impressum" (not hidden under "Kontakt"/"AGB")
- Not behind a login, not requiring scripts to read

## Output (in German)

```
# Impressum-Prüfung: <URL/Quelle>

## Gesamturteil
<vollständig / Lücken / kritisch — 1–2 Sätze, inkl. Erreichbarkeit>

## Pflichtangaben
| Angabe | Status | Rechtsgrundlage | Befund / Fix |
|--------|--------|-----------------|--------------|
| Vertretungsberechtigter | fehlt | § 5 DDG (Zitat) | Ergänzen: Geschäftsführer … |
| Telefon/zweiter Kanal | vorhanden | § 5 DDG (Zitat) | ok |

## Platzierung
<Erreichbarkeit, Beschriftung, Ein-Klick-Regel>

## Empfehlung
<priorisierte Schritte; fehlende Angaben als einfügbarer Textblock>
```

"Rechtsgrundlage" must quote § 5 DDG text returned by `get-article`. Where a
business detail is unknown, mark it `[Platzhalter]` rather than inventing it.

## After

Offer to: assemble a complete ready-to-paste Impressum block, run
`datenschutz-review` (the privacy policy is a separate duty), or run
`website-scan`.

## Boundaries

Decision-support, not legal advice — say so once. Regulated professions and
journalistic offerings carry extra duties; flag those and recommend a lawyer or
the relevant Kammer rather than asserting completeness.
