#!/usr/bin/env python3
"""Extract the Mahnwesen-relevant fields from a German structured e-invoice.

Deterministic, stdlib-only. Reads an XRechnung / ZUGFeRD CII (UN/CEFACT
CrossIndustryInvoice) XML and emits the EN 16931 fields the e-rechnung-mahnwesen
skill needs to draft a §286 BGB dunning: invoice number, issue date, due date,
amount due, currency, seller, buyer — plus a Verzug (days overdue) calculation.

This does NOT validate EN16931/XRechnung conformance — that needs the KoSIT
validator / Mustangproject Schematron (Java). This is the parse step only.

Usage:
  python3 parse_einvoice.py <invoice.xml> [--asof YYYY-MM-DD]

--asof fixes the reference date for the Verzug calc (defaults to today). Pass it
for deterministic output (tests, reproducible drafts).
"""
import sys
import json
import argparse
import datetime
import xml.etree.ElementTree as ET

NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}


def _text(root, path):
    el = root.find(path, NS)
    return el.text.strip() if el is not None and el.text else None


def _date102(root, path):
    """Read a UN/CEFACT format-102 date (YYYYMMDD) -> ISO YYYY-MM-DD."""
    raw = _text(root, path)
    if not raw or len(raw) != 8:
        return None
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"


def parse(xml_path, asof=None):
    root = ET.parse(xml_path).getroot()
    tx = "rsm:SupplyChainTradeTransaction/"
    settle = tx + "ram:ApplicableHeaderTradeSettlement/"
    agree = tx + "ram:ApplicableHeaderTradeAgreement/"

    due = _date102(root, settle
                   + "ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString")
    out = {
        "invoice_number": _text(root, "rsm:ExchangedDocument/ram:ID"),                 # BT-1
        "issue_date": _date102(root, "rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString"),  # BT-2
        "due_date": due,                                                               # BT-9
        "amount_due": _text(root, settle
                            + "ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:DuePayableAmount"),  # BT-115
        "currency": _text(root, settle + "ram:InvoiceCurrencyCode"),                   # BT-5
        "seller": _text(root, agree + "ram:SellerTradeParty/ram:Name"),                # BT-27
        "buyer": _text(root, agree + "ram:BuyerTradeParty/ram:Name"),                  # BT-44
    }

    # Verzug: days overdue relative to --asof (or today).
    ref = datetime.date.fromisoformat(asof) if asof else datetime.date.today()
    if due:
        days = (ref - datetime.date.fromisoformat(due)).days
        out["days_overdue"] = days
        out["in_verzug"] = days > 0
    else:
        out["days_overdue"] = None
        out["in_verzug"] = None
    out["asof"] = ref.isoformat()

    missing = [k for k in ("invoice_number", "due_date", "amount_due") if not out[k]]
    out["missing_required"] = missing
    return out


def main():
    ap = argparse.ArgumentParser(description="Extract Mahnwesen fields from a CII e-invoice.")
    ap.add_argument("invoice")
    ap.add_argument("--asof", help="reference date YYYY-MM-DD for the Verzug calc")
    args = ap.parse_args()
    try:
        result = parse(args.invoice, args.asof)
    except (ET.ParseError, FileNotFoundError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
