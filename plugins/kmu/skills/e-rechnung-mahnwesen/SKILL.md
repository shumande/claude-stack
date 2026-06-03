---
name: e-rechnung-mahnwesen
description: Handle a German company's invoicing flow — read an incoming E-Rechnung (XRechnung/ZUGFeRD), check outgoing invoices for Pflichtangaben, and draft a staged, legally-grounded Mahnwesen for overdue invoices under §286 BGB. Use when someone asks to process an invoice, chase an overdue payment, set up dunning, or check an invoice for completeness. Legal anchors are cited from official sources (gesetze-im-internet.de for §286/§288 BGB, BMF for the §14 UStG E-Rechnung obligation) — not from memory. Every client-facing draft pauses for human approval.
argument-hint: "<invoice file/text or 'overdue: <details>'>"
---

# E-Rechnung & Mahnwesen

> Connectors/tools: [CONNECTORS.md](../../CONNECTORS.md). This skill uses **no MCP** —
> both legal anchors are outside the dsgvo.pro catalog, so they are cited from
> official free sources. External operator tooling (Mustangproject/KoSIT for
> parsing/validation) is documented in [feasibility-e-rechnung.md](../../docs/feasibility-e-rechnung.md).

Operator skill for the invoicing routine of a German B2B firm. Two jobs:
**(1) E-Rechnung** — read an incoming structured invoice or sanity-check an outgoing
one for Pflichtangaben; **(2) Mahnwesen** — turn an overdue invoice into a correct,
escalation-staged dunning sequence grounded in §286 BGB. This is the door-opener of
the KMU toolkit: the E-Rechnung-Pflicht (since 01.01.2025) is a legal deadline every
B2B firm must meet, and overdue invoices are felt-pain cashflow.

## Trigger

"Process this invoice", "is this Rechnung complete", "this customer hasn't paid",
"set up / draft a Mahnung", "Zahlungserinnerung", "chase overdue invoices".

## Inputs

1. **The invoice** — an XRechnung (XML), a ZUGFeRD PDF (PDF/A-3 with embedded XML),
   or pasted invoice text; OR, for dunning, the overdue facts: Betrag,
   Rechnungsnummer, Rechnungsdatum, Fälligkeitsdatum, which reminders already went
   out, and whether a Zahlungsziel/Verzug clause was agreed.
2. **The relationship** — a valued long-term client or a repeat late payer? This sets
   the TONE of the Mahnung. A valued client gets a subtle, high-quality reminder that
   preserves the Vertrauensverhältnis; never jump to Inkasso/Betreibung for them
   without the operator's explicit say-so.

## Grounding step (do this first) — official sources, NO MCP

- **Mahnwesen/Verzug:** cite **§ 286 BGB** (Verzug des Schuldners) and **§ 288 BGB**
  (Verzugszinsen; §288(5) 40€ B2B-Verzugspauschale) from **gesetze-im-internet.de**
  (`https://www.gesetze-im-internet.de/bgb/__286.html`,
  `https://www.gesetze-im-internet.de/bgb/__288.html`). Quote the relevant sentence as
  the Rechtsgrundlage. Do **not** call the dsgvo.pro MCP — its "BGB" is a
  digital/consumer subset that does not contain §286/§288 (verified Phase 0).
- **E-Rechnung-Pflicht:** cite the **BMF** — since **01.01.2025** every domestic B2B
  must be able to **RECEIVE** structured e-invoices; issuing phases in: **<800k€**
  Vorjahresumsatz exempt through end of **2027**, **>800k€** must issue from
  **01.01.2027**; paper/other allowed generally through **31.12.2026**. Legal basis:
  §14 UStG / Wachstumschancengesetz. Source:
  `https://www.bundesfinanzministerium.de/Content/DE/FAQ/e-rechnung.html`. Not memory.

## Pflichtangaben check (outgoing invoice)

Verify the §14 UStG mandatory items (catalog is settled; cite BMF, not memory): full
name+address of both parties, USt-IdNr or Steuernummer, Ausstellungsdatum,
fortlaufende Rechnungsnummer, Menge/Art der Leistung, Leistungszeitpunkt, Entgelt +
applicable USt-Satz/-Betrag (or Hinweis on Steuerbefreiung / Reverse-Charge /
Kleinunternehmer §19 UStG). For structured formats, confirm the file parses as valid
XRechnung/ZUGFeRD — the authoritative check is the KoSIT validator / Mustangproject
Schematron (see feasibility doc); do not assert validity from a glance.

## Field extraction (deterministic — for structured invoices)

Do not eyeball amounts and dates out of XML. Run the bundled parser — it handles
**all three carriers** (XRechnung CII XML, XRechnung UBL XML, and ZUGFeRD/Factur-X
**PDF/A-3** with embedded XML):

```
# XML: stdlib only
python3 plugins/kmu/scripts/parse_einvoice.py <invoice.xml> [--asof YYYY-MM-DD]
# ZUGFeRD PDF: use the venv (pikepdf); set up once: python3 -m venv scripts/.venv && scripts/.venv/bin/pip install -r scripts/requirements.txt
plugins/kmu/scripts/.venv/bin/python plugins/kmu/scripts/parse_einvoice.py <invoice.pdf>
```

Returns JSON: `syntax` (CII/UBL), `invoice_number` (BT-1), `issue_date` (BT-2),
`due_date` (BT-9), `amount_due` (BT-115), `currency`, `seller`, `buyer`,
`days_overdue`, `in_verzug`, `missing_required`. Use those exact values in the
Mahnung — never re-type them. If `due_date` is in `missing_required`, the invoice
carries no BT-9; ask the operator for the agreed Zahlungsziel before computing Verzug.

## Validation (authoritative, optional)

For a real EN16931 / XRechnung conformance check (not just parsing), run the
Mustangproject validator. It needs Java + the Mustang jar (one-time
`bash scripts/fetch-mustang.sh`):

```
python3 plugins/kmu/scripts/validate_einvoice.py <invoice.pdf|.xml>
```

Returns `{status: valid|invalid, errors:[...]}`, exit 0 when valid. Use this before
treating an OUTGOING invoice as compliant. If Java/jar are absent it returns
`status: unavailable` — then note the validation was skipped (do not claim valid).

## Mahnwesen — staged sequence (grounded)

Draft, do not send. Default 3-stage escalation, tone set by the relationship:

1. **Zahlungserinnerung** — freundlich, no Verzug language yet. For valued clients
   this is often enough.
2. **1. Mahnung** — references/establishes Verzug per §286 BGB (quote the provision),
   names a concrete Frist.
3. **2./letzte Mahnung** — adds Verzugszinsen (§288 BGB) and the §288(5)
   Verzugspauschale (40€, B2B), warns of further steps. Never threaten
   Inkasso/Betreibung for a valued client without explicit operator approval.

## Output (in German)

```
# Rechnungs-/Mahnvorgang: <Rechnungsnr. / Quelle>

## Status & Befund
<E-Rechnung gültig? Pflichtangaben vollständig? Überfällig seit? Beziehungston>

## Rechtsgrundlage
<§286/§288 BGB Zitat (gesetze-im-internet.de); E-Rechnung-Pflicht: Quelle BMF>

## Entwurf (zur Freigabe)
<vollständiger Mahn-/Erinnerungstext, einfügefertig — als ENTWURF markiert>

## Nächster Schritt
<welche Stufe, welche Frist, was bei Nichtzahlung folgt>
```

"Rechtsgrundlage" must quote the actual §286/§288 BGB wording from
gesetze-im-internet.de. Unknown business facts → `[Platzhalter]`, never invented.

## After (HUMAN CHECKPOINT)

Present the draft and STOP. Ask the operator to approve/edit before it is treated as
sent. Then offer: escalate to the next Mahnstufe, run `buchhaltung-datev-layer` to log
the open item, or check the Datenschutz of the dunning channel via the `dsgvo` plugin.

## Boundaries

Decision-support, not Rechtsberatung — say so once. Inkasso/Betreibung and court steps
are out of scope; recommend a lawyer/Inkasso-Dienstleister rather than drafting those.
Never auto-send.
