#!/usr/bin/env python3
"""Seed categorization of common German B2B-Dienstleister transactions to DATEV
chart-of-accounts numbers (SKR03 and SKR04).

Numbers verified line-by-line against the official DATEV Standardkontenrahmen PDFs
(gültig 2025) by the spec workflow (2026-06-03). One number is NOT fully confirmed —
SKR04 6310 (Miete/Raumkosten); it is flagged `verify=True` and must be checked against
the SKR04 PDF before relying on it.

This is a SEED, not a complete chart. It exists to draft a Gegenkonto suggestion that
the operator (and ultimately the Steuerberater) confirms — never to auto-book.
"""
import re
import json
import sys
import argparse

# (label, skr03, skr04, keyword, verify_flag)
# ORDER MATTERS: first match wins, so more-specific (multi-word) keywords must precede
# the single-word keyword they are a superset of (e.g. Reisekosten Unternehmer before
# the generic Reisekosten).
SEED = [
    ("Erlöse 19% USt",                      "8400", "4400", "erlös",            False),
    ("Bürobedarf",                          "4930", "6815", "bürobedarf",       False),
    ("Telefon/Telekommunikation",           "4920", "6805", "telefon",          False),
    ("Raumkosten/Miete",                    "4200", "6310", "miete",            True),  # SKR04 6310 unverified
    ("Reisekosten Unternehmer",             "4670", "6670", "reisekosten unternehmer", False),
    ("Reisekosten Arbeitnehmer",            "4660", "6650", "reisekosten",      False),
    ("Bewirtungskosten",                    "4650", "6640", "bewirtung",        False),
    ("Fremdleistungen",                     "3100", "5900", "fremdleistung",    False),
    ("Werbekosten",                         "4600", "6600", "werbung",          False),
    ("Fahrzeugkosten (Sammel)",             "4500", "6500", "kfz",              False),
    ("Laufende Fahrzeug-Betriebskosten",    "4530", "6530", "tankstelle",       False),
    ("Versicherungen (betrieblich)",        "4360", "6400", "versicherung",     False),
    ("EDV-Software (Anlage/Lizenz)",        "0027", "0135", "software lizenz",  False),
    ("Wartung Hard-/Software (lfd.)",       "4806", "6495", "wartung",          False),
    ("Nebenkosten Geldverkehr (Bank)",      "4970", "6855", "bankgebühr",       False),
    ("Rechts- und Beratungskosten",         "4950", "6825", "beratung",         False),
    ("Löhne und Gehälter",                  "4100", "6000", "lohn",             False),
    ("Gesetzliche soziale Aufwendungen",    "4130", "6110", "sozialversicherung", False),
    ("Abschreibungen auf Sachanlagen",      "4830", "6220", "abschreibung",     False),
    ("Abziehbare Vorsteuer 19%",            "1576", "1406", "vorsteuer",        False),
    ("Umsatzsteuer 19%",                    "1776", "3806", "umsatzsteuer",     False),
]


def categorize(text, chart="skr03"):
    """Return the best account suggestion for a transaction description.

    Returns dict {account, label, keyword, verify, confident}. `confident` is False
    when no keyword matched (caller must ask the operator).
    """
    idx = 1 if chart.lower() == "skr03" else 2
    t = (text or "").lower()
    # Match each keyword word at a word START (\b before), free suffix after — so German
    # inflections (Bankgebühren, Reisekosten) match, but mid-word false positives don't.
    def has(word):
        return re.search(r"\b" + re.escape(word), t) is not None
    for label, a03, a04, kw, verify in SEED:
        if all(has(w) for w in kw.split()):
            return {"account": (a03 if idx == 1 else a04), "label": label,
                    "keyword": kw, "verify": verify, "confident": True}
    return {"account": None, "label": None, "keyword": None, "verify": False,
            "confident": False}


def main():
    ap = argparse.ArgumentParser(description="Categorize a transaction to an SKR account.")
    ap.add_argument("text", nargs="?", help="transaction description")
    ap.add_argument("--chart", default="skr03", choices=["skr03", "skr04"])
    ap.add_argument("--dump", action="store_true", help="print the full seed table")
    args = ap.parse_args()
    if args.dump or not args.text:
        print(json.dumps([{"label": l, "skr03": a3, "skr04": a4, "keyword": k,
                           "verify": v} for l, a3, a4, k, v in SEED],
                         ensure_ascii=False, indent=2))
        return
    print(json.dumps(categorize(args.text, args.chart), ensure_ascii=False))


if __name__ == "__main__":
    main()
