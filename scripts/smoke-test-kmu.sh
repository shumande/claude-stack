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

# e-invoice parser actually runs on the sample fixture and extracts the right fields
sample="plugins/kmu/skills/e-rechnung-mahnwesen/examples/sample-xrechnung-cii.xml"
if out=$(python3 plugins/kmu/scripts/parse_einvoice.py "$sample" --asof 2026-06-03 2>/dev/null); then
  python3 -c "
import json,sys
d=json.loads('''$out''')
assert d['invoice_number']=='RE-2026-00417', d['invoice_number']
assert d['due_date']=='2026-04-29', d['due_date']
assert d['days_overdue']==35, d['days_overdue']
assert d['in_verzug'] is True
assert d['missing_required']==[]
" && echo "ok parser: extracts fields + Verzug=35d" || { echo "BAD parser output"; fail=1; }
else
  echo "PARSER FAILED to run"; fail=1
fi

[ "$fail" -eq 0 ] && echo "ALL PASS" || { echo "FAILURES"; exit 1; }
