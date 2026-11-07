#!/usr/bin/env python3
"""founder-board.json -> markdown для памяти gbrain. Только month, tails, received. Без реквизитов."""
import json, sys, re
src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src))
L = ["# Доска ПУЛЬТ (выжимка для памяти)", "", f"Обновлено: {d.get('updated')}. Источник: plans/founder-board.json (истина по деньгам и цели месяца; карточки клиентов могут отставать).", ""]
m = d["month"]
L += [f"## Месяц: {m['label']}", "", m["note"], ""]
for g in m.get("goals", []):
    L.append(f"- Цель: {g['name']} — факт {g.get('fact')} из {g.get('target')}" + (f", срок {g['due']}" if g.get("due") else "") + (" (€ нетто)" if g.get("eur") else ""))
L += ["", "## Хвосты (ждём оплату, не получено)", ""]
for t in d["tails"]:
    L.append(f"### НЕ ОПЛАЧЕНО: {t['project']}")
    for k, n in (("what", "Что"), ("money", "Сумма € нетто"), ("since", "С"), ("move", "Ход"), ("client", "Клиент"), ("invoice", "Счёт"), ("checked", "Сверено")):
        if t.get(k) is not None: L.append(f"- {n}: {t[k]}")
    L.append("")
L += ["## Получено: эти платежи ОПЛАЧЕНЫ, деньги пришли", ""]
for r in d["received"]:
    L.append(f"- ОПЛАЧЕНО, деньги получены {r['date']} · клиент {r['client']}" + (f" · счёт #{r['invoice']}" if r.get("invoice") else "") + f" · нетто {r.get('net')} €" + (f" · брутто {r['gross']} €" if r.get("gross") else "") + f" — {r.get('source','')}")
txt = "\n".join(L) + "\n"
bad = re.findall(r"\bDE\d{2}[ \d]{15,}|IBAN|BIC\b|sk-[A-Za-z0-9]{16,}", txt)
if bad: sys.exit(f"реквизиты в выводе: {bad}")
open(out, "w").write(txt)
print(len(txt), "bytes")
