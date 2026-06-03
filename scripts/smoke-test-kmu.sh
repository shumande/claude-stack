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
