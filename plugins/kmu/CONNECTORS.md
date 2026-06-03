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

**External tooling (operator-side, not MCP):** Mustangproject + KoSIT validator for
reading/validating XRechnung/ZUGFeRD (needs a JRE); DATEV-EXTF Buchungsstapel CSV for
the Steuerberater hand-off. See `docs/feasibility-e-rechnung.md` and
`docs/feasibility-datev.md`.

**Human checkpoint:** every skill that produces a client-facing artifact (invoice,
Mahnung, hand-off pack) MUST present a draft and wait for the operator to approve
before it is treated as sent/final.
