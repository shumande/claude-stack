# Feasibility — Buchhaltung DATEV-Layer (Phase 0, 2026-06-03)

**Verdict: GO** — the v1 hand-off pack ("ingest receipts/bank export → categorize to
SKR03/04 → emit EXTF Buchungsstapel + open-items/missing-receipts list → hand to
Steuerberater, **no write-back**") is shippable as a TURNKEY skill. Every input and the
output sit on open/free or merely plan-paywalled rails with **zero DATEV partnership
dependency** — the Steuerberater's own DATEV does the import.

## Capability table

| Capability | Verdict | Why | Source |
|---|---|---|---|
| Write bookings into DATEV via API | **OUT-OF-SCOPE** | Cloud APIs need partner onboarding + certification (paid/gated); core write is async EXTF/dxso batch jobs, reached practically only via certified unified-API resellers | apideck.com; developer.datev.de; maesn.com |
| Generate valid EXTF Buchungsstapel CSV (no DATEV software) | **TURNKEY** | EXTF is DATEV's documented CSV exchange format, spec free on Developer Portal; proven by open-source generators | developer.datev.de/file-format; github.com/ledermann/datev |
| Exact EXTF field layout (header + ~125 cols, encoding) | **PLAYBOOK / verify-first** | Format open but canonical field table is JS-gated (blank to fetcher). Confirm version (5.10 / file-version "700"=7.0), header order, ANSI/Win-1252 encoding, `;` delimiter, date masks before shipping | developer.datev.de/file-format/header; github.com/ledermann/datev |
| Steuerberater imports the file | **TURNKEY** | EXTF .csv imported via DATEV Rechnungswesen Stapelverarbeitung — standard built-in; third-party files accepted | ah.consulting; conaktiv handbuch |
| SKR03 / SKR04 mapping target | **TURNKEY** | Both charts published by DATEV as free yearly PDFs (2026 live); account numbers public | datev.de standard-kontenrahmen |
| sevDesk: read transactions/vouchers + export | **TURNKEY (paywalled)** | Open documented REST API; gate = Buchhaltung Pro plan, API token, no certification | api.sevdesk.de |
| lexware office: read vouchers/payments + export | **TURNKEY (paywalled)** | Public REST `api.lexware.io`, OAuth2; gate = XL plan. **Bank-tx reads need Partner API = PLAYBOOK/OUT** → use CAMT/CSV bank import instead | developers.lexware.io |
| Bank export ingest (CSV / CAMT.053) | **TURNKEY** | CAMT.053 = ISO 20022 XML standard (DK migration to v08 2025/26), open/parseable; CSV trivial | inwerken.de; probankconvert.com |

## ⚠️ Pre-build gate (not a blocker)

Treat the **exact EXTF field layout as verify-first PLAYBOOK**: the canonical spec
pages (`developer.datev.de/de/file-format/...`) are JavaScript-rendered and returned
blank to automated fetch. The format is confirmed **open and free** (plus a free DATEV
test program for CSV files), and open libs encode it — but read the field table in a
real browser / via DATEV's test program and **validate generated files before
declaring the skill done.** Do not trust any second-hand field summary as byte-exact.

## Honest access flags

- **DATEV cloud API** = genuinely gated (certification, paid onboarding) → correctly
  avoided by the hand-off design (this exclusion is what makes v1 shippable).
- **EXTF spec** = free but JS-gated to automated tools; openness confirmed second-hand.
- **sevDesk** read = needs Buchhaltung Pro; **lexware** public read = needs XL plan,
  and **bank-transaction** reads need the gated Partner API → sidestep via CAMT/CSV.

## GO/NO-GO

**GO** — ship as a "hand-off pack" skill, no write-back. The only OUT-OF-SCOPE piece
(programmatic DATEV write-back) is exactly what the design already excludes. One
pre-build gate: verify the EXTF field layout against the canonical spec / DATEV test
program before marking the skill done.
