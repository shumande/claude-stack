# Feasibility — E-Rechnung / Mahnwesen (Phase 0, 2026-06-03)

**Verdict: GO** — ship `e-rechnung-mahnwesen` as the first skill. Mahnwesen +
incoming-parsing + Pflichtangaben-validation are all TURNKEY on free, open tooling.
Outgoing e-invoice generation is PLAYBOOK (scope as "validate/wrap an exported
invoice", not "we are your invoicing system").

## Capability table

| Capability | Verdict | Tool / why | Source |
|---|---|---|---|
| Read/extract XML from incoming ZUGFeRD PDF | **TURNKEY** | Mustangproject CLI extract; Python `drafthorse`/`factur-x` | mustangproject.org/use |
| Read incoming XRechnung XML (CII/UBL) | **TURNKEY** | Same CII parsers; Mustang supports CII XRechnung 3.0.2 | github.com/ZUGFeRD/mustangproject |
| Validate invoice (EN16931 + XRechnung Pflichtangaben) | **TURNKEY** | KoSIT validator (official) + Mustang Schematron | github.com/itplr-kosit/validator |
| Extract dunning fields (amount BT-112/115, due date BT-9, invoice no BT-1, parties) | **TURNKEY** | Standard EN16931 BT-codes; parse once, map | github.com/pretix/python-drafthorse |
| Generate outgoing e-invoice from scratch | **PLAYBOOK** | Libs serialize valid XML, but invoice data + gapless numbering + tax/legal correctness live in client's billing tool | github.com/ZUGFeRD/mustangproject |
| XRechnung generation specifically | **PLAYBOOK** | No official generator; some Py/Node libs lack XRechnung profile | github.com/zfutura/pycheval |
| Mahnwesen / Verzug logic | **TURNKEY** | Pure date+amount arithmetic on parsed fields | (legal source below) |

**Formats:** XRechnung = pure XML (B2G-dominant, Peppol/Leitweg-ID). ZUGFeRD =
hybrid PDF/A-3 + embedded XML (B2B practical default). Both EN 16931-compliant;
CII XML is shared, so one parser reads both.

**Open tooling confirmed real:** Mustangproject (Apache-2.0 Java lib/CLI/server,
v2.23.1 2026-05-28 — read/validate/create/convert), KoSIT `validator` +
`validator-configuration-xrechnung` (official). Python: `drafthorse` (pretix),
`factur-x` (akretion), `pycheval` (no XRechnung yet). Node: `node-zugferd` (v0.0.x,
young), `@stackforge-eu/factur-x`. PHP: `horstoeko/zugferd`.

**Honest weak spots:** best validate/generate tooling is Java → skill likely shells
out to a bundled jar (plan for a JRE dependency). XRechnung generation in Py/Node is
thin; treat non-Java generation output as unvalidated until run through KoSIT/Mustang.
Node `node-zugferd` is v0.0.x, not production-grade for issuance.

## ⚠️ Legal grounding — CORRECTION to the plan (caught in Phase 0)

The plan assumed **§286 BGB grounds live via the dsgvo.pro MCP. It does NOT.**
Verified 2026-06-03:
- `get-article(law=bgb, article=286)` → `"Article/paragraph 286 not found in BGB"`.
- `search-law(law=bgb, "Verzug Schuldner Mahnung")` → 0 results.
- The dsgvo.pro **"BGB" is a curated digital/consumer subset** (only e.g. §312
  Anwendungsbereich, §356a Elektronische Widerrufsfunktion) — **not the full code.**
  §286/§288 Verzug are outside the catalog.

**Consequence:** the `e-rechnung-mahnwesen` skill does **NOT** use the dsgvo.pro MCP.
Both its legal anchors are cited from official free sources, never from memory:
- **Mahnwesen/Verzug:** §286 BGB + §288 BGB (Verzugszinsen, §288(5) 40€ B2B-Pauschale)
  → cite **gesetze-im-internet.de** (`/bgb/__286.html`, `/bgb/__288.html`).
- **E-Rechnung-Pflicht:** §14 UStG / Wachstumschancengesetz → cite **BMF**
  (bundesfinanzministerium.de/Content/DE/FAQ/e-rechnung.html).

→ **Update Phase 2 SKILL.md "Grounding step" and the plugin CONNECTORS.md** to drop
the dsgvo.pro dependency for this skill. dsgvo.pro stays the grounding engine for the
separate `dsgvo` (compliance) plugin, woven in only when a DSGVO question arises.

## Legal facts — confirmed from BMF FAQ E-Rechnung

- **Empfangspflicht seit 01.01.2025** — every domestic B2B must be able to RECEIVE
  structured e-invoices.
- **Ausstellung:** paper/other allowed through **31.12.2026** (general transition).
- **>800k€ Vorjahresumsatz** → must ISSUE e-invoices from **01.01.2027**;
  **<800k€** exempt through end of **2027**. EDI usable through end of 2027.
- **Rechtsgrundlage:** §14 UStG neu gefasst via Wachstumschancengesetz; BMF-Schreiben
  15.10.2024 + 15.10.2025.
Source: https://www.bundesfinanzministerium.de/Content/DE/FAQ/e-rechnung.html

## GO/NO-GO

**GO** for Mahnwesen + incoming-parse + validation (turnkey, free Apache tooling).
Outgoing generation = PLAYBOOK ("validate/wrap exported invoice"). Structural caveat:
JRE dependency for authoritative validation — acceptable for a back-office operator tool.

## IMPLEMENTED 2026-06-03

- `scripts/parse_einvoice.py` — parses **CII + UBL XML + ZUGFeRD/Factur-X PDF** (embedded
  XML via pikepdf), extracts BT-1/2/9/115 + parties, computes Verzug. Tested on real
  fixtures incl. the mustangproject `EN16931_Einfach.pdf` (extracted invoice 471102,
  €529.87; correctly flagged the missing BT-9). UBL legal names via PartyLegalEntity/
  RegistrationName (not PartyName/Name).
- `scripts/validate_einvoice.py` + `scripts/fetch-mustang.sh` — authoritative EN16931/
  XRechnung validation via Mustang CLI (Java); ran `status=valid` on the sample.
- All covered by `scripts/smoke-test-kmu.sh` (PDF + validation gated on deps).
- Outgoing-generation stays PLAYBOOK by design (client's billing tool).
