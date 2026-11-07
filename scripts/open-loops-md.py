#!/usr/bin/env python3
"""Открытые петли по клиенту и по человеку для памяти gbrain.
Ход/стадия — из карточек clients/*.md (frontmatter), деньги — ТОЛЬКО из founder-board.json (карточки по деньгам отстают).
Использование: open-loops-md.py <founder-board.json> <clients-dir> <out.md>"""
import json, re, sys, glob, os
board, cdir, out = sys.argv[1:4]
d = json.load(open(board))
PEOPLE = {"Виталием (Seehaus, Obere Mühle, Lebensart)": ["seehaus", "obere-muehle", "lebensart"]}
def fm(path):
    t = open(path).read()
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    r = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1); r[k.strip()] = v.strip()
    return r
cards = {os.path.basename(p)[:-3]: fm(p) for p in glob.glob(f"{cdir}/*.md") if not p.endswith("README.md")}
tails = {}
for t in d["tails"]:
    tails.setdefault(t.get("client"), []).append(t)
paid = {}
for r in d["received"]:
    paid.setdefault(r["client"], []).append(r)
def block(cid):
    c = cards.get(cid, {})
    L = [f"### {c.get('client', cid)}", f"- Стадия: {c.get('stage','⬜')}; чей ход: {c.get('whose_move','⬜')} (карточка обновлена {c.get('updated','⬜')})", f"- Следующий ход: {c.get('next_move','⬜')}"]
    for t in tails.get(cid, []):
        L.append(f"- НЕ ОПЛАЧЕНО (доска): {t['what']}" + (f" — {t['money']} € нетто" if t.get("money") else ""))
    if not tails.get(cid): L.append("- Неоплаченных счетов на доске нет.")
    for r in paid.get(cid, []):
        L.append(f"- ОПЛАЧЕНО (доска): {r['date']}" + (f" счёт #{r['invoice']}" if r.get("invoice") else "") + f", нетто {r.get('net')} €")
    L.append("- Деньги — по доске выше; поле money в карточке может отставать.")
    return L + [""]
L = ["# Открытые петли по клиентам и людям (выжимка для памяти)", "", f"Доска обновлена {d.get('updated')}. Ход и стадия — из карточек clients/*, деньги — только из доски.", ""]
L += ["## Открыто по человеку", ""]
for name, ids in PEOPLE.items():
    L += [f"## Что открыто с {name}", ""]
    for cid in ids: L += block(cid)
L += ["## Открыто по клиентам", ""]
for cid in sorted(cards):
    if not any(cid in v for v in PEOPLE.values()): L += block(cid)
txt = "\n".join(L) + "\n"
if re.search(r"\bDE\d{2}[ \d]{15,}|IBAN|sk-[A-Za-z0-9]{16,}", txt): sys.exit("реквизиты в выводе")
open(out, "w").write(txt); print(len(txt), "bytes")
