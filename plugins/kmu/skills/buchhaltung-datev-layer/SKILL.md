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

## What it does (TURNKEY per feasibility-datev.md)

- Extract + normalize each transaction (Datum, Betrag, USt, Gegenkonto-Vorschlag).
- Categorize against the SKR03/SKR04 chart (both are publicly documented by DATEV);
  mark low-confidence rows for review.
- Flag gaps: missing receipts, uncategorizable items, USt inconsistencies, possible
  duplicates.
- Produce a **DATEV-EXTF / Buchungsstapel** export the Steuerberater can import via
  DATEV Stapelverarbeitung, plus a plain-German open-items + missing-receipts list for
  the owner.

> **Pre-build gate (operator note):** the exact EXTF field layout (header order,
> Win-1252 encoding, `;` delimiter, version "700"/5.10, date masks) must be validated
> against the canonical DATEV spec / free DATEV test program before any generated file
> is sent — the spec page is JS-gated. Do not assume a byte-exact layout from memory.

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
