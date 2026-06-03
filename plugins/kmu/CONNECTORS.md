# KMU plugin — connectors & tools

This plugin uses **no MCP**. Both legal anchors of its skills are outside the
dsgvo.pro catalog (verified Phase 0, 2026-06-03), so skills cite official free
sources directly — never from memory.

| Skill | Grounding | Source | MCP? |
|-------|-----------|--------|------|
| e-rechnung-mahnwesen | §286 / §288 BGB (Verzug, Verzugszinsen) | gesetze-im-internet.de | No |
| e-rechnung-mahnwesen | E-Rechnung-Pflicht (§14 UStG) | bundesfinanzministerium.de (BMF FAQ) | No |
| buchhaltung-datev-layer | DATEV-EXTF format, SKR03/04 | developer.datev.de, datev.de | No |

**Why no dsgvo.pro MCP:** the dsgvo.pro "BGB" is a curated digital/consumer subset
(§312, §356a) — it does **not** carry §286/§288 BGB Verzug, and §14 UStG is not in
the catalog at all. The dsgvo.pro MCP stays the grounding engine of the separate
`dsgvo` (compliance) plugin; weave that plugin in only when a DSGVO question arises.

## Bundled tooling (operator-side scripts, not MCP)

| Script | Does | Deps |
|--------|------|------|
| `scripts/parse_einvoice.py` | Extract EN16931 fields + Verzug from XRechnung CII/UBL XML or ZUGFeRD PDF | stdlib (XML); pikepdf for PDF |
| `scripts/gen_extf.py` | Generate DATEV-EXTF Buchungsstapel CSV (byte-verified) | stdlib |
| `scripts/skr.py` | Categorize a transaction → SKR03/SKR04 account (seed) | stdlib |
| `scripts/validate_einvoice.py` | Authoritative EN16931/XRechnung validation | Java + Mustang jar |

**One-time setup for the optional bits:**
- ZUGFeRD-PDF extraction: `python3 -m venv plugins/kmu/scripts/.venv && plugins/kmu/scripts/.venv/bin/pip install -r plugins/kmu/scripts/requirements.txt` (pikepdf).
- Authoritative validation: `bash scripts/fetch-mustang.sh` (downloads the ~58 MB Mustang CLI jar; needs a JRE — `brew install openjdk`).

The `.venv/` and `vendor/Mustang-CLI.jar` are git-ignored (heavy/local). XML parsing,
EXTF generation and SKR categorization work with plain `python3`, no extra deps.
All four are exercised by `scripts/smoke-test-kmu.sh` (PDF + validation gated on deps).

**Human checkpoint:** every skill that produces a client-facing artifact (invoice,
Mahnung, hand-off pack) MUST present a draft and wait for the operator to approve
before it is treated as sent/final.
