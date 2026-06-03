#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
echo "== kmu plugin smoke test =="
EX=plugins/kmu/skills/e-rechnung-mahnwesen/examples
S=plugins/kmu/scripts
VENV="$S/.venv/bin/python"
JAR="$S/vendor/Mustang-CLI.jar"

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
  else echo "skip (deferred): $s"; fi
done

# human checkpoint in every client-facing skill (must also carry STOP/approve language)
for f in plugins/kmu/skills/*/SKILL.md; do
  if grep -qi 'HUMAN CHECKPOINT' "$f" && grep -qiE 'STOP|approve|Freigabe|bestätig' "$f"; then
    echo "ok checkpoint: $f"
  else echo "NO human checkpoint+approve: $f"; fail=1; fi
done

# --- e-invoice parser: CII (stdlib) ---
python3 "$S/parse_einvoice.py" "$EX/sample-xrechnung-cii.xml" --asof 2026-06-03 \
  | python3 -c "import json,sys;d=json.load(sys.stdin);assert d['syntax']=='CII' and d['invoice_number']=='RE-2026-00417' and d['days_overdue']==35 and d['missing_required']==[]" \
  && echo "ok parse CII: RE-2026-00417, 35d" || { echo "BAD CII parse"; fail=1; }

# --- e-invoice parser: UBL (stdlib) ---
python3 "$S/parse_einvoice.py" "$EX/sample-ubl-xrechnung.xml" --asof 2026-06-30 \
  | python3 -c "import json,sys;d=json.load(sys.stdin);assert d['syntax']=='UBL' and d['invoice_number']=='RE-2026-00042' and d['seller']=='Muster Dienstleistungen GmbH' and d['buyer']=='Beispiel Bau AG' and d['days_overdue']==14" \
  && echo "ok parse UBL: RE-2026-00042, legal names, 14d" || { echo "BAD UBL parse"; fail=1; }

# --- DATEV-EXTF generator: structure + FULL data-row match vs ledermann reference ---
python3 "$S/gen_extf.py" 2>/dev/null | python3 -c "
import sys, csv, io
ls=[l for l in sys.stdin.read().split('\r\n') if l]
fields=lambda l: next(csv.reader(io.StringIO(l), delimiter=';', quotechar='\"'))
assert len(fields(ls[0]))==31, 'header field count'
assert len(fields(ls[1]))==125, 'colname field count'
row=fields(ls[2])
assert len(row)==125, 'data field count'
ref=['24,95','H','','','','','1200','4940','8','2102','','','','Fachbuch: Controlling für Dummies']
assert row[:14]==ref, 'data first-14 != reference'
assert all(f=='' for f in row[14:]), 'data fields 15-125 not all empty'
" && echo "ok gen_extf: 31/125/125 fields, FULL data row matches DATEV reference" || { echo "BAD EXTF gen"; fail=1; }

# EXTF encoding: cp1252, no BOM, CRLF
python3 "$S/gen_extf.py" -o /tmp/_kmu_extf.csv && python3 -c "
d=open('/tmp/_kmu_extf.csv','rb').read()
assert d[:3]!=b'\xef\xbb\xbf', 'has BOM'
assert b'f\xfcr' in d, 'umlaut not cp1252 0xFC'
assert d.endswith(b'\r\n'), 'not CRLF-terminated'
" && echo "ok gen_extf: cp1252, no BOM, CRLF" || { echo "BAD EXTF encoding"; fail=1; }

# --- EXTF with real header params (no demo placeholders) ---
python3 "$S/gen_extf.py" --berater 7777 --mandant 123 --wj-beginn 20260101 --datum-von 20260401 --datum-bis 20260430 2>/dev/null \
  | python3 -c "
import sys, csv, io
h=next(csv.reader(io.StringIO(sys.stdin.read().split('\r\n')[0]),delimiter=';',quotechar='\"'))
assert h[10]=='7777' and h[11]=='123', (h[10],h[11])
" && echo "ok gen_extf: real Berater/Mandant via CLI" || { echo "BAD header params"; fail=1; }

# --- SKR categorization ---
python3 "$S/skr.py" "Rechtsanwalt Beratung" --chart skr04 \
  | python3 -c "import json,sys;d=json.load(sys.stdin);assert d['account']=='6825' and d['confident']" \
  && echo "ok skr: Beratung -> 6825 (SKR04)" || { echo "BAD skr"; fail=1; }
python3 "$S/skr.py" "Reisekosten Unternehmer Hotel" --chart skr03 \
  | python3 -c "import json,sys;d=json.load(sys.stdin);assert d['account']=='4670', d['account']" \
  && echo "ok skr: Reisekosten Unternehmer -> 4670 (not shadowed)" || { echo "BAD skr shadow"; fail=1; }

# --- GATED: ZUGFeRD-PDF extraction (needs venv+pikepdf) ---
if [ -x "$VENV" ] && "$VENV" -c "import pikepdf" 2>/dev/null; then
  "$VENV" "$S/parse_einvoice.py" "$EX/sample-zugferd.pdf" --asof 2026-06-03 \
    | python3 -c "import json,sys;d=json.load(sys.stdin);assert d['syntax']=='CII' and d['amount_due']=='529.87' and d['due_date'] is None and 'due_date' in d['missing_required']" \
    && echo "ok parse ZUGFeRD-PDF: real embedded XML, 529.87 EUR, missing-BT9 flagged" || { echo "BAD PDF parse"; fail=1; }
else
  echo "skip (no venv/pikepdf): ZUGFeRD-PDF extraction"
fi

# --- GATED: authoritative Mustang validation (needs Java + jar) ---
if [ -f "$JAR" ] && { command -v java >/dev/null 2>&1 || [ -x /opt/homebrew/opt/openjdk/bin/java ]; }; then
  MUSTANG_JAVA="${MUSTANG_JAVA:-/opt/homebrew/opt/openjdk/bin/java}" \
    python3 "$S/validate_einvoice.py" "$EX/sample-zugferd.pdf" >/dev/null 2>&1 \
    && echo "ok validate: Mustang status=valid (exit 0)" || { echo "BAD validation"; fail=1; }
else
  echo "skip (no jar/java — run scripts/fetch-mustang.sh): EN16931 validation"
fi

[ "$fail" -eq 0 ] && echo "ALL PASS" || { echo "FAILURES"; exit 1; }
