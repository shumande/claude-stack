---
name: buchhaltung-datev-layer
description: Prepare clean pre-accounting for a German firm's Steuerberater — ingest receipts/bank exports, categorize transactions, flag gaps, and produce a DATEV-ready hand-off pack (EXTF Buchungsstapel) plus an open-items list. It works ON TOP of the firm's existing DATEV/sevDesk/lexoffice — it does NOT replace them and does NOT file taxes. Use when someone asks to sort receipts, prepare the month for the Steuerberater, or clean up bookkeeping data. Produces a draft hand-off for human approval.
argument-hint: "<receipts/bank export, or 'Monatsabschluss <month>'>"
---

# Buchhaltung — DATEV-Layer (Steuerberater hand-off)

> Connectors/tools: [CONNECTORS.md](../../CONNECTORS.md). Uses no MCP. Scope is
> bounded by [feasibility-datev.md](../../docs/feasibility-datev.md) — read it first.

Operator skill that buys back the service-firm owner's billable hours by taking the
pre-accounting drudgery off their desk. It **prepares and hands off** clean data to
the Steuerberater; it is explicitly **not** an accounting program and **not** a tax
filing. This boundary is the whole product — it disarms both the "overlap with my
Steuerberater" objection (we feed them, not replace them) and the vaporware objection
(we promise a hand-off pack, not magic).

## Trigger

"Sort these receipts", "prepare the month for my Steuerberater", "categorize these
transactions", "Monatsabschluss vorbereiten", "clean up the books".

## Inputs

1. **The raw data** — receipts (photo/PDF), bank export (CSV or CAMT.053 XML), and any
   existing Kontenrahmen the Steuerberater uses (SKR03 or SKR04).
2. **Context** — Kleinunternehmer §19 or USt-pflichtig? Which import format does the
   Steuerberater expect (DATEV-EXTF Buchungsstapel is the default)?

## What it does

Two tiers — keep them honest:

**AI-assisted (read the output critically — no deterministic script):**
- Ingest the inputs: read receipts (photo/PDF — there is **no OCR script**, the agent
  reads them) and the bank export (CSV / CAMT.053), and normalize each transaction
  (Datum, Betrag, USt, Gegenkonto-Vorschlag). Treat these extractions as drafts.

**Deterministic (scripted, verified):**
- **Categorize** to SKR03/SKR04 with the seed mapping:
  `python3 plugins/kmu/scripts/skr.py "<Buchungstext>" --chart skr03|skr04` → returns
  the suggested account; `confident:false` means no keyword matched → ask the operator.
  Mark `verify:true` rows (e.g. SKR04 6310 Miete) for the operator to confirm.
- Flag gaps: missing receipts, uncategorizable items, USt inconsistencies, duplicates.
- **Produce the DATEV-EXTF Buchungsstapel** the Steuerberater imports via DATEV
  Stapelverarbeitung:
  `python3 plugins/kmu/scripts/gen_extf.py --bookings bookings.json -o Stapel.csv`
  where `bookings.json` is a list of `{umsatz, soll_haben, konto, gegenkonto,
  bu_schluessel, belegdatum, belegfeld1, buchungstext}`. The generator is **byte-verified**
  against the ledermann/datev reference and DATEV Dok.-Nr. 1003221 (31-field header,
  125-field rows, Windows-1252, CRLF, `;`, comma-decimals, DDMM Belegdatum) — see
  [feasibility-datev.md](../../docs/feasibility-datev.md).

> **Operator confirms before import:** the SKR seed is a starter chart (~20 categories;
> SKR04 6310 not fully verified) and the EXTF header metadata (Berater/Mandant/WJ) must
> be the client's real numbers. Generate the draft, let the operator/Steuerberater
> confirm accounts and metadata, then import. Never auto-book.

## What it does NOT do (state this every run)

Does not write into DATEV (programmatic write-back needs gated DATEV partnership — out
of scope), does not file USt-Voranmeldung/EÜR, does not give Steuerberatung. Those stay
with the Steuerberater (StBerG-Vorbehalt).

## Output (in German)

```
# Buchhaltungs-Vorbereitung: <Monat/Quelle>

## Übersicht
<Anzahl Belege, Summe, Anteil sicher kategorisiert, offene Punkte>

## Zur Klärung (vor Übergabe)
<fehlende Belege, unsichere Buchungen, USt-Auffälligkeiten — als Liste>

## Übergabe-Paket (Entwurf)
<Verweis auf erzeugte DATEV-EXTF-Datei + Klartext-Zusammenfassung>

## Hinweis
Dies ersetzt nicht Ihren Steuerberater. Keine Steuerberatung (StBerG).
```

## After (HUMAN CHECKPOINT)

Present the hand-off pack as a DRAFT and STOP. The operator reviews the flagged items
and approves before anything goes to the Steuerberater. Then offer:
`e-rechnung-mahnwesen` for the open receivables, or a DSGVO check of the data-handling
via the `dsgvo` plugin.

## Boundaries

Pre-accounting support, not Buchführung/Steuerberatung (StBerG-Vorbehalt). If the data
implies a tax judgment, route it to the Steuerberater — do not decide it.
