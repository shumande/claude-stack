# KMU-Plugin — First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the first slice of a German KMU Claude-Code plugin (`claude-stack/plugins/kmu`) — the two skills validated by atypica as the wedge for a B2B-service-firm owner: **E-Rechnung/Mahnwesen** (door-opener) and **Buchhaltung-DATEV-Layer** (closer) — plus scaffold and a wiring to the existing `dsgvo` plugin.

**Architecture:** A new `kmu` plugin inside the existing `claude-stack` marketplace, mirroring the proven `dsgvo` plugin structure (`.claude-plugin/plugin.json` + `skills/<name>/SKILL.md`). Skills are **operator-facing** — they are Alexey's delivery toolkit for the "embedded AI employee" service, not a self-install product for the non-technical client. Each skill produces a German client-facing artifact and **pauses for human approval before anything leaves the building** (CTA-canon: "die KI führt die Routine, der Mensch bestätigt das Kritische"). Legal citations are pulled live from the dsgvo.pro MCP where the statute is in its catalog; where it is not (e.g. §14 UStG), the skill says so and cites the official source instead of inventing.

**Tech Stack:** Claude Code plugin format (Markdown SKILL.md + frontmatter), dsgvo.pro MCP (`get-article` / `search-law`, free tier), bash smoke-test. No application code, no build step.

---

## ⚠️ Architecture decision to confirm (single most important assumption)

This plan assumes **operator-toolkit model**: the plugin is run BY Alexey (or his agent) to deliver done-for-you outcomes to clients. The non-technical service-firm owner never installs Claude Code. This is driven by the ЦА (service owners won't install plugins) and the positioning ("embedded employee, recurring, done-for-you").

If instead the intent is **client-self-install**, the whole skill ergonomics change (onboarding, auth, guardrails) and this plan must be reworked. **One-line veto point — confirm before Phase 1.**

Source of truth for priority/wedge: [ai-firma-landing-app3/research/2026-06-03_atypica-validation.md](../../../ai-firma-landing-app3/research/2026-06-03_atypica-validation.md). Order: E-Rechnung → DATEV-Layer → DSGVO(reuse, woven-in) → Kundenkontakt(deferred).

---

## File Structure

```
claude-stack/
  .claude-plugin/marketplace.json        # MODIFY: add "kmu" plugin entry
  plugins/kmu/
    .claude-plugin/plugin.json           # CREATE: kmu plugin manifest
    CONNECTORS.md                         # CREATE: which MCP tools each skill uses
    skills/
      e-rechnung-mahnwesen/SKILL.md       # CREATE: door-opener skill
      buchhaltung-datev-layer/SKILL.md    # CREATE: closer skill (feasibility-gated)
    docs/
      feasibility-e-rechnung.md           # CREATE (Phase 0 output): turnkey vs playbook
      feasibility-datev.md                # CREATE (Phase 0 output): DATEV reality
      anti-picks.md                       # CREATE: what we deliberately do NOT do
  scripts/
    smoke-test-kmu.sh                     # CREATE: validates kmu skills load + ground
```

**Out of scope for this slice (explicit defer):** `kundenkontakt` skill (atypica: dead-last + relationship risk → redesign as internal triage later), the broader small-business skills (margin, payroll, crm, content), pricing-page, landing build.

---

## Phase 0 — Feasibility gate (do this BEFORE authoring skills)

Rationale: atypica's #1 trust-killer is **vaporware**. The #2-priority DATEV-Layer is the technically riskiest (no public DATEV MCP). We settle turnkey-vs-playbook on paper before any SKILL.md promises an outcome.

### Task 0a: E-Rechnung feasibility spike

**Files:**
- Create: `plugins/kmu/docs/feasibility-e-rechnung.md`

- [ ] **Step 1: Investigate the structured-invoice reality.** Answer in the doc, with sources: (a) the two German formats — **XRechnung** (XML) and **ZUGFeRD** (hybrid PDF/A-3 + XML); (b) is there an open library/CLI to read+validate+generate these (e.g. Mustangproject for ZUGFeRD, KoSIT validator for XRechnung)? (c) what is genuinely automatable by an operator agent (parse incoming XRechnung → extract Verzug-relevant fields; generate a compliant outgoing invoice) vs what needs the client's existing tool. Mark each capability **TURNKEY** / **PLAYBOOK** / **OUT-OF-SCOPE**.

- [ ] **Step 2: Settle the legal grounding split.** Record explicitly: **Mahnwesen/Verzug = §286 BGB** → groundable via dsgvo.pro MCP (BGB is in catalog). **E-Rechnung-Pflicht = §14 UStG / Wachstumschancengesetz** → NOT in dsgvo.pro catalog → skill must cite BMF (bundesfinanzministerium.de e-rechnung FAQ) and say so. Verify §286 BGB is retrievable: run the MCP call below and paste the returned text.

Run: `get-article` (dsgvo-pro MCP) for `§ 286 BGB`.
Expected: returns Verzug des Schuldners text. If not found, fall back to `search-law "Verzug Mahnung"` and record the correct article id.

- [ ] **Step 3: Go/No-Go.** Write a one-paragraph verdict: is E-Rechnung/Mahnwesen shippable as a turnkey-enough first skill? (Expected: YES for the Mahnwesen half + incoming-invoice parsing; the outgoing-format generation may be PLAYBOOK depending on Step 1.) Commit.

```bash
git add plugins/kmu/docs/feasibility-e-rechnung.md
git commit -m "docs(kmu): e-rechnung feasibility — turnkey vs playbook"
```

### Task 0b: DATEV-Layer feasibility spike

**Files:**
- Create: `plugins/kmu/docs/feasibility-datev.md`

- [ ] **Step 1: Investigate DATEV/sevDesk/lexoffice integration surface.** Answer with sources: (a) does DATEV expose a usable API for third parties (DATEVconnect / DATEV-API marketplace) and what does it gate behind partnership? (b) sevDesk and lexoffice REST APIs — what's openly available? (c) the realistic operator move: the "DATEV-Layer" prepares/categorizes/exports data FOR the Steuerberater (DATEV-Buchungsstapel CSV/EXTF format) rather than writing INTO DATEV. Mark capabilities TURNKEY / PLAYBOOK / OUT-OF-SCOPE.

- [ ] **Step 2: Define the honest scope of the v1 DATEV-Layer skill.** Most likely TURNKEY core = "ingest receipts/bank exports → categorize → produce a clean DATEV-EXTF / pre-accounting hand-off pack + open-items list" (no write-back into DATEV). Record exactly what the skill will and will NOT claim. This directly prevents the vaporware objection.

- [ ] **Step 3: Go/No-Go.** Verdict paragraph: is the DATEV-Layer shippable in this slice, or does it become a documented PLAYBOOK skill (operator runs steps semi-manually, presents turnkey outcome)? Commit.

```bash
git add plugins/kmu/docs/feasibility-datev.md
git commit -m "docs(kmu): datev-layer feasibility — hand-off pack scope"
```

**Gate:** If Task 0b verdict = OUT-OF-SCOPE for v1, drop Phase 3 from this slice and ship E-Rechnung alone; record the deferral in `anti-picks.md` (Task 6).

---

## Phase 1 — Plugin scaffold

### Task 1: Register the `kmu` plugin in the marketplace

**Files:**
- Modify: `.claude-plugin/marketplace.json` (the `plugins` array)

- [ ] **Step 1: Add the kmu entry.** Append this object to the `plugins` array (after the existing `dsgvo` object — mind the comma):

```json
    {
      "name": "kmu",
      "displayName": "KMU AI-Mitarbeiter",
      "source": "./plugins/kmu",
      "category": "business",
      "description": "Operator toolkit for a DSGVO-konform 'AI-Mitarbeiter' for the German Mittelstand: handle incoming/outgoing E-Rechnung and Mahnwesen (§286 BGB), and prepare clean Buchhaltung hand-off for the Steuerberater. Built for B2B-Dienstleister owners. Legal citations pulled live via the dsgvo.pro MCP; every client-facing output pauses for human approval.",
      "homepage": "https://ai-firma.de"
    }
```

- [ ] **Step 2: Validate JSON.** Run: `python3 -c "import json,sys; json.load(open('.claude-plugin/marketplace.json'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit.**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(kmu): register kmu plugin in marketplace"
```

### Task 2: Create the kmu plugin manifest + CONNECTORS

**Files:**
- Create: `plugins/kmu/.claude-plugin/plugin.json`
- Create: `plugins/kmu/CONNECTORS.md`

- [ ] **Step 1: Write `plugins/kmu/.claude-plugin/plugin.json`:**

```json
{
  "name": "kmu",
  "version": "0.1.0",
  "description": "Operator toolkit for a DSGVO-konform AI-Mitarbeiter for the German Mittelstand: E-Rechnung & Mahnwesen (§286 BGB) and Buchhaltung hand-off for the Steuerberater. Legal citations pulled live from the dsgvo.pro MCP; client-facing outputs pause for human approval.",
  "author": {
    "name": "shumande",
    "url": "https://ai-firma.de"
  },
  "homepage": "https://ai-firma.de"
}
```

- [ ] **Step 2: Write `plugins/kmu/CONNECTORS.md`** documenting which tools each skill needs:

```markdown
# KMU plugin — connectors & tools

| Skill | Tool | Provider | Key needed? |
|-------|------|----------|-------------|
| e-rechnung-mahnwesen | — (no MCP) | official sources | n/a — cites gesetze-im-internet.de + BMF |
| buchhaltung-datev-layer | — (no MCP) | official sources | n/a |

**⚠ Corrected in Phase 0 (2026-06-03):** the dsgvo.pro MCP grounds NEITHER legal
anchor of these skills. Verified: dsgvo.pro "BGB" is a curated digital/consumer
subset (§312, §356a) — **§286/§288 BGB Verzug are NOT in it**; §14 UStG is not
either. So this plugin's skills use NO MCP and cite official free sources:
**§286/§288 BGB → gesetze-im-internet.de**, **§14 UStG E-Rechnung-Pflicht → BMF
FAQ**. The dsgvo.pro MCP stays the engine of the separate `dsgvo` plugin, woven in
only when a DSGVO question arises. See
[docs/feasibility-e-rechnung.md](docs/feasibility-e-rechnung.md).

**Human checkpoint:** every skill that produces a client-facing artifact
(invoice, Mahnung, hand-off pack) MUST present a draft and wait for the operator
to approve before it is treated as sent/final.
```

- [ ] **Step 3: Validate JSON + commit.**

Run: `python3 -c "import json; json.load(open('plugins/kmu/.claude-plugin/plugin.json'))" && echo OK`
Expected: `OK`

```bash
git add plugins/kmu/.claude-plugin/plugin.json plugins/kmu/CONNECTORS.md
git commit -m "feat(kmu): plugin manifest + connectors doc"
```

---

## Phase 2 — Skill: e-rechnung-mahnwesen (the door-opener)

### Task 3: Author the e-rechnung-mahnwesen SKILL.md

**Files:**
- Create: `plugins/kmu/skills/e-rechnung-mahnwesen/SKILL.md`

- [ ] **Step 1: Write the full SKILL.md** (this is the complete content — no placeholders):

````markdown
---
name: e-rechnung-mahnwesen
description: Handle a German company's invoicing flow — read an incoming E-Rechnung (XRechnung/ZUGFeRD), check outgoing invoices for Pflichtangaben, and draft a staged, legally-grounded Mahnwesen for overdue invoices under §286 BGB. Use when someone asks to process an invoice, chase an overdue payment, set up dunning, or check an invoice for completeness. Mahnung legal basis pulled live via the dsgvo.pro MCP; E-Rechnung obligation cited from the BMF. Every client-facing draft pauses for human approval.
argument-hint: "<invoice file/text or 'overdue: <details>'>"
---

# E-Rechnung & Mahnwesen

> Connectors/tools: [CONNECTORS.md](../../CONNECTORS.md). Uses NO MCP — both legal
> anchors are cited from official free sources (dsgvo.pro does not carry §286 BGB
> or §14 UStG; verified Phase 0).

Operator skill for the invoicing routine of a German B2B firm. Two jobs:
**(1) E-Rechnung** — read an incoming structured invoice or sanity-check an
outgoing one for Pflichtangaben; **(2) Mahnwesen** — turn an overdue invoice
into a correct, escalation-staged dunning sequence grounded in §286 BGB.

## Trigger

"Process this invoice", "is this Rechnung complete", "this customer hasn't paid",
"set up / draft a Mahnung", "Zahlungserinnerung", "chase overdue invoices".

## Inputs

1. **The invoice** — an XRechnung (XML), a ZUGFeRD PDF (PDF/A-3 with embedded
   XML), or pasted invoice text; OR, for dunning, the overdue facts: amount,
   Rechnungsnummer, Rechnungsdatum, Fälligkeitsdatum, what reminders already went
   out, and whether a Zahlungsziel/Verzug clause was agreed.
2. **The relationship** — is this a valued long-term client or a repeat late
   payer? This sets the TONE of the Mahnung (Beat's rule: a subtle high-quality
   reminder preserves the Vertrauensverhältnis; never jump to Betreibung).

## Grounding step (do this first) — official sources, NO MCP

- For any dunning: cite **§ 286 BGB** (Verzug des Schuldners) and **§ 288 BGB**
  (Verzugszinsen; §288(5) 40€ B2B-Verzugspauschale) from
  **gesetze-im-internet.de** (`/bgb/__286.html`, `/bgb/__288.html`). The dsgvo.pro
  MCP does NOT carry these (its "BGB" is a digital/consumer subset — verified
  Phase 0), so do not call it for this skill.
- **E-Rechnung obligation:** cite the BMF — since 01.01.2025 every domestic B2B
  must be able to RECEIVE structured e-invoices; issuing phases in (>800k€ Umsatz
  from 01.01.2027, <800k€ exempt through end 2027); legal basis §14 UStG /
  Wachstumschancengesetz. Source: bundesfinanzministerium.de, not memory.

## Pflichtangaben check (outgoing invoice)

Verify the invoice carries the §14 UStG mandatory items (catalog is settled;
cite BMF, not MCP): full name+address of both parties, USt-IdNr or Steuernummer,
Ausstellungsdatum, fortlaufende Rechnungsnummer, Menge/Art der Leistung,
Leistungszeitpunkt, Entgelt + applicable USt-Satz/-Betrag (or Hinweis on
Steuerbefreiung / Reverse-Charge / Kleinunternehmer §19 UStG). For structured
formats, confirm it parses as valid XRechnung/ZUGFeRD (per
[feasibility-e-rechnung.md](../../docs/feasibility-e-rechnung.md)).

## Mahnwesen — staged sequence (grounded)

Draft, do not send. Default 3-stage escalation, tone set by the relationship:
1. **Zahlungserinnerung** (freundlich, no Verzug language yet) — for valued
   clients this is often enough.
2. **1. Mahnung** — establishes/【references Verzug per §286 BGB (quote the
   article), names a concrete Frist.
3. **2. Mahnung / letzte** — adds Verzugszinsen (§288 BGB) + the §288(5)
   Verzugspauschale (40€, B2B), warns of further steps. Never threaten
   Betreibung/Inkasso for a valued client without explicit operator approval.

## Output (in German)

```
# Rechnungs-/Mahnvorgang: <Rechnungsnr. / Quelle>

## Status & Befund
<E-Rechnung gültig? Pflichtangaben vollständig? Überfällig seit? Beziehungston>

## Rechtsgrundlage
<§286 BGB Zitat aus get-article; E-Rechnung-Pflicht: Quelle BMF>

## Entwurf (zur Freigabe)
<der vollständige Mahn-/Erinnerungstext, einfügefertig — als ENTWURF markiert>

## Nächster Schritt
<welche Stufe, welche Frist, was bei Nichtzahlung folgt>
```

"Rechtsgrundlage" must quote the §286 BGB text returned by `get-article`. Unknown
business facts → `[Platzhalter]`, never invented.

## After (HUMAN CHECKPOINT)

Present the draft and STOP. Ask the operator to approve/edit before it is treated
as sent. Then offer: escalate to the next Mahnstufe, run `buchhaltung-datev-layer`
to log the open item, or check the Datenschutz of the dunning channel via the
`dsgvo` plugin.

## Boundaries

Decision-support, not Rechtsberatung — say so once. Inkasso/Betreibung and
court steps are out of scope; recommend a lawyer/Inkasso-Dienstleister rather
than drafting those. Never auto-send.
````

- [ ] **Step 2: Validate frontmatter parses.** Run:
`python3 -c "import re,sys; t=open('plugins/kmu/skills/e-rechnung-mahnwesen/SKILL.md').read(); fm=re.match(r'^---\n(.*?)\n---', t, re.S); assert fm and 'name: e-rechnung-mahnwesen' in fm.group(1) and 'description:' in fm.group(1); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Grounding smoke-check (manual, via MCP).** In a Claude session with the dsgvo-pro MCP, run the `get-article` call for §286 BGB and confirm it returns Verzug text (proves the Grounding step is real, not aspirational). Record the returned article id/text snippet as a comment at the bottom of `feasibility-e-rechnung.md`.

- [ ] **Step 4: Commit.**

```bash
git add plugins/kmu/skills/e-rechnung-mahnwesen/SKILL.md
git commit -m "feat(kmu): e-rechnung-mahnwesen skill (§286 BGB grounded)"
```

---

## Phase 3 — Skill: buchhaltung-datev-layer (the closer) — GATED on Task 0b

> Only do Phase 3 if Task 0b verdict ≠ OUT-OF-SCOPE. If gated out, skip to Phase 4 and record the defer in anti-picks.

### Task 4: Author the buchhaltung-datev-layer SKILL.md

**Files:**
- Create: `plugins/kmu/skills/buchhaltung-datev-layer/SKILL.md`

- [ ] **Step 1: Write the full SKILL.md** (scope strictly to what Task 0b marked TURNKEY — the hand-off pack, NOT write-back into DATEV):

````markdown
---
name: buchhaltung-datev-layer
description: Prepare clean pre-accounting for a German firm's Steuerberater — ingest receipts/bank exports, categorize transactions, flag gaps, and produce a DATEV-ready hand-off pack (EXTF/Buchungsstapel) plus an open-items list. It works ON TOP of the firm's existing DATEV/sevDesk/lexoffice — it does NOT replace them and does NOT file taxes. Use when someone asks to sort receipts, prepare the month for the Steuerberater, or clean up bookkeeping data. Produces a draft hand-off for human approval.
argument-hint: "<receipts/bank export, or 'Monatsabschluss <month>'>"
---

# Buchhaltung — DATEV-Layer (Steuerberater hand-off)

> Connectors/tools: [CONNECTORS.md](../../CONNECTORS.md). Scope is bounded by
> [feasibility-datev.md](../../docs/feasibility-datev.md) — read it first.

Operator skill that buys back the service-firm owner's billable hours by taking
the pre-accounting drudgery off their desk. It **prepares and hands off** clean
data to the Steuerberater; it is explicitly **not** an accounting program and
**not** a tax filing. This boundary is the whole product — it disarms both the
"overlap with my Steuerberater" objection (we feed them, not replace them) and
the vaporware objection (we promise a hand-off pack, not magic).

## Trigger

"Sort these receipts", "prepare the month for my Steuerberater", "categorize
these transactions", "Monatsabschluss vorbereiten", "clean up the books".

## Inputs

1. **The raw data** — receipts (photo/PDF), bank export (CSV/CAMT), and any
   existing chart-of-accounts (Kontenrahmen SKR03/SKR04) the Steuerberater uses.
2. **Context** — Kleinunternehmer §19 or USt-pflichtig? Which Steuerberater
   software/format do they expect (DATEV EXTF Buchungsstapel is the default)?

## What it does (TURNKEY per feasibility-datev.md)

- Extract + normalize each transaction (Datum, Betrag, USt, Gegenkonto-Vorschlag).
- Categorize against the SKR03/SKR04 chart; mark low-confidence rows for review.
- Flag gaps: missing receipts, uncategorizable items, USt inconsistencies,
  possible duplicates.
- Produce a **DATEV-EXTF / Buchungsstapel** export the Steuerberater can import,
  plus a plain-German open-items + missing-receipts list for the owner.

## What it does NOT do (state this every run)

Does not write into DATEV, does not file USt-Voranmeldung/EÜR, does not give
Steuerberatung. Those stay with the Steuerberater (StBerG-Vorbehalt).

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

Present the hand-off pack as a DRAFT and STOP. Operator reviews the flagged items
and approves before anything goes to the Steuerberater. Then offer:
`e-rechnung-mahnwesen` for the open receivables, or a DSGVO check of the
data-handling via the `dsgvo` plugin.

## Boundaries

Pre-accounting support, not Buchführung/Steuerberatung (StBerG-Vorbehalt). If the
data implies a tax judgment, route it to the Steuerberater — do not decide it.
````

- [ ] **Step 2: Validate frontmatter.** Run:
`python3 -c "import re; t=open('plugins/kmu/skills/buchhaltung-datev-layer/SKILL.md').read(); fm=re.match(r'^---\n(.*?)\n---',t,re.S); assert fm and 'name: buchhaltung-datev-layer' in fm.group(1); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit.**

```bash
git add plugins/kmu/skills/buchhaltung-datev-layer/SKILL.md
git commit -m "feat(kmu): buchhaltung-datev-layer skill (Steuerberater hand-off, no write-back)"
```

---

## Phase 4 — Wiring, anti-picks, smoke test

### Task 5: Smoke test for the kmu plugin

**Files:**
- Create: `scripts/smoke-test-kmu.sh`

- [ ] **Step 1: Write the script** (mirrors the existing `scripts/smoke-test.sh` pattern — validates structure + frontmatter, does not call the network):

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
echo "== kmu plugin smoke test =="

# manifest present + valid JSON
for f in plugins/kmu/.claude-plugin/plugin.json .claude-plugin/marketplace.json; do
  python3 -c "import json;json.load(open('$f'))" && echo "ok json: $f" || { echo "BAD json: $f"; fail=1; }
done

# marketplace references kmu
grep -q '"name": "kmu"' .claude-plugin/marketplace.json && echo "ok: kmu registered" || { echo "MISSING kmu in marketplace"; fail=1; }

# each skill has frontmatter name+description
for s in e-rechnung-mahnwesen buchhaltung-datev-layer; do
  f="plugins/kmu/skills/$s/SKILL.md"
  if [ -f "$f" ]; then
    python3 -c "import re;t=open('$f').read();fm=re.match(r'^---\n(.*?)\n---',t,re.S);assert fm and 'name: $s' in fm.group(1) and 'description:' in fm.group(1)" \
      && echo "ok skill: $s" || { echo "BAD frontmatter: $s"; fail=1; }
  else
    echo "skip (gated/deferred): $s"
  fi
done

# every client-facing skill must declare a human checkpoint
for f in plugins/kmu/skills/*/SKILL.md; do
  grep -qi 'HUMAN CHECKPOINT' "$f" && echo "ok checkpoint: $f" || { echo "NO human checkpoint: $f"; fail=1; }
done

[ "$fail" -eq 0 ] && echo "ALL PASS" || { echo "FAILURES"; exit 1; }
```

- [ ] **Step 2: Make executable + run.**

Run: `chmod +x scripts/smoke-test-kmu.sh && ./scripts/smoke-test-kmu.sh`
Expected: ends with `ALL PASS` (the `buchhaltung-datev-layer` line shows `skip` if Phase 3 was gated out).

- [ ] **Step 3: Commit.**

```bash
git add scripts/smoke-test-kmu.sh
git commit -m "test(kmu): smoke test for structure + human-checkpoint guarantee"
```

### Task 6: Anti-picks doc (what we deliberately do NOT build)

**Files:**
- Create: `plugins/kmu/docs/anti-picks.md`

- [ ] **Step 1: Write it** — capture the atypica-driven exclusions so the next builder doesn't re-add them:

```markdown
# KMU plugin — anti-picks (validated exclusions)

Driven by atypica validation 2026-06-03 (panel 63572). We deliberately do NOT:

- **Lead with DSGVO as the wedge.** DSGVO is hygiene + the #1 objection, not the
  door-opener. It is woven into every skill (audit trail, EU-host, human-in-loop)
  and lives in the separate `dsgvo` plugin — not the headline. Wedge = E-Rechnung.
- **Ship a client-facing Kundenkontakt bot.** Validated dead-last and a
  relationship-killer for service firms ("the bridge I built over 20 years is
  crumbling"). If revisited, ONLY as internal lead-triage, never a bot the
  client's customers talk to.
- **Replace DATEV/sevDesk/lexoffice.** We sit ON TOP and hand off; replacing them
  loses the "complementary to my Steuerberater" trust and over-promises.
- **Auto-send anything.** Every client-facing artifact pauses for human approval.
- **Use the slogan "der Mitarbeiter, der nie kündigt".** Rejected as hype.
  Landing/offer language = "Rechtssicher, kein Abmahn-Risiko" + concrete proof.
- **Claim MCP grounding for §14 UStG.** Not in the dsgvo.pro catalog — cite BMF.
```

- [ ] **Step 2: Commit.**

```bash
git add plugins/kmu/docs/anti-picks.md
git commit -m "docs(kmu): anti-picks from atypica validation"
```

---

## Self-Review (run after writing — done)

**Spec coverage:** atypica priority order → Phase 2 (E-Rechnung opener) + Phase 3
(DATEV closer) + anti-picks (DSGVO-as-hygiene, no Kundenkontakt bot). Feasibility
risk (no DATEV MCP) → Phase 0 gate. Human-checkpoint CTA-canon → enforced in every
skill + asserted by smoke test. Legal-grounding honesty (§286 BGB via MCP, §14 UStG
via BMF) → CONNECTORS + both skills. ✔ covered.

**Placeholder scan:** SKILL.md bodies are complete; `[Platzhalter]` appears only as
the intentional German marker for unknown business facts, not as a plan gap. ✔

**Type/name consistency:** skill names `e-rechnung-mahnwesen` / `buchhaltung-datev-layer`
identical across marketplace, plugin.json mentions, file paths, smoke test, and
frontmatter. ✔

**Open item (not a gap, a decision):** operator-toolkit vs client-install — flagged
at top for one-line confirmation before Phase 1.
```
```
