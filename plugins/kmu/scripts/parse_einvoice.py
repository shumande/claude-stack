#!/usr/bin/env python3
"""Extract the Mahnwesen-relevant fields from a German structured e-invoice.

Handles all three carriers the e-rechnung-mahnwesen skill meets:
  - XRechnung CII (UN/CEFACT CrossIndustryInvoice) XML
  - XRechnung UBL (OASIS Invoice-2) XML
  - ZUGFeRD / Factur-X PDF/A-3 (embedded XML extracted via pikepdf)

Emits the EN 16931 fields needed to draft a §286 BGB dunning (invoice number, issue
date, due date, amount due, currency, seller, buyer) plus a Verzug (days overdue) calc.

It does NOT validate EN16931/XRechnung conformance — that needs the KoSIT validator /
Mustangproject Schematron (see validate_einvoice.py). This is the parse step only.

Usage:
  python3 parse_einvoice.py <invoice.xml|invoice.pdf> [--asof YYYY-MM-DD]

PDF input requires pikepdf (see scripts/.venv). XML input is stdlib-only.
--asof fixes the reference date for the Verzug calc (defaults to today).
"""
import sys
import json
import argparse
import datetime
import xml.etree.ElementTree as ET

CII = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}
UBL = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

# ZUGFeRD 2.x/Factur-X, ZUGFeRD 1.0, XRechnung-in-PDF embedded filenames.
EMBEDDED_NAMES = ["factur-x.xml", "zugferd-invoice.xml", "xrechnung.xml"]


def _text(root, path, ns):
    el = root.find(path, ns)
    return el.text.strip() if el is not None and el.text and el.text.strip() else None


def _date102(raw):
    """UN/CEFACT format-102 date (YYYYMMDD) -> ISO YYYY-MM-DD."""
    if not raw or len(raw) != 8:
        return None
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"


def parse_cii(root):
    tx = "rsm:SupplyChainTradeTransaction/"
    settle = tx + "ram:ApplicableHeaderTradeSettlement/"
    agree = tx + "ram:ApplicableHeaderTradeAgreement/"
    return {
        "syntax": "CII",
        "invoice_number": _text(root, "rsm:ExchangedDocument/ram:ID", CII),
        "issue_date": _date102(_text(root, "rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString", CII)),
        "due_date": _date102(_text(root, settle + "ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString", CII)),
        "amount_due": _text(root, settle + "ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:DuePayableAmount", CII),
        "currency": _text(root, settle + "ram:InvoiceCurrencyCode", CII),
        "seller": _text(root, agree + "ram:SellerTradeParty/ram:Name", CII),
        "buyer": _text(root, agree + "ram:BuyerTradeParty/ram:Name", CII),
    }


def parse_ubl(root):
    # BT-9: invoice-level cbc:DueDate first, fallback cac:PaymentMeans/cbc:PaymentDueDate
    due = _text(root, "cbc:DueDate", UBL) or _text(root, "cac:PaymentMeans/cbc:PaymentDueDate", UBL)
    # BT-27/44: legal name is PartyLegalEntity/RegistrationName (NOT PartyName/Name)
    return {
        "syntax": "UBL",
        "invoice_number": _text(root, "cbc:ID", UBL),
        "issue_date": _text(root, "cbc:IssueDate", UBL),           # already ISO
        "due_date": due,
        "amount_due": _text(root, "cac:LegalMonetaryTotal/cbc:PayableAmount", UBL),
        "currency": _text(root, "cbc:DocumentCurrencyCode", UBL),
        "seller": _text(root, "cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", UBL)
                  or _text(root, "cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", UBL),
        "buyer": _text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", UBL)
                 or _text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", UBL),
    }


def _embedded_xml_from_pdf(pdf_path):
    """Extract the EN16931 XML bytes from a ZUGFeRD/Factur-X PDF/A-3 via pikepdf."""
    try:
        import pikepdf
    except ImportError:
        sys.exit("PDF input needs pikepdf — run with the venv: "
                 "plugins/kmu/scripts/.venv/bin/python (pip install pikepdf)")
    with pikepdf.open(pdf_path) as pdf:
        att = pdf.attachments
        lower = {k.lower(): k for k in att.keys()}
        for want in EMBEDDED_NAMES:
            if want.lower() in lower:
                return att[lower[want.lower()]].get_file().read_bytes()
        for key in att.keys():
            if key.lower().endswith(".xml"):
                return att[key].get_file().read_bytes()
        # low-level /Names/EmbeddedFiles fallback
        names = pdf.Root.get("/Names")
        if names is not None and "/EmbeddedFiles" in names:
            tree = pikepdf.NameTree(names.EmbeddedFiles)
            for _, spec in tree.items():
                ef = spec["/EF"]
                stream = ef.get("/UF") or ef.get("/F")
                if stream is not None:
                    return stream.read_bytes()
    raise ValueError("No embedded e-invoice XML found in PDF")


def load_root(path):
    if path.lower().endswith(".pdf"):
        data = _embedded_xml_from_pdf(path)
        return ET.fromstring(data)
    return ET.parse(path).getroot()


def parse(path, asof=None):
    root = load_root(path)
    tag = root.tag.split("}")[-1]  # local name
    if tag == "CrossIndustryInvoice":
        out = parse_cii(root)
    elif tag == "Invoice":
        out = parse_ubl(root)
    else:
        raise ValueError(f"Unrecognized invoice root <{tag}> (expected CrossIndustryInvoice or Invoice)")

    ref = datetime.date.fromisoformat(asof) if asof else datetime.date.today()
    if out["due_date"]:
        days = (ref - datetime.date.fromisoformat(out["due_date"])).days
        out["days_overdue"], out["in_verzug"] = days, days > 0
    else:
        out["days_overdue"], out["in_verzug"] = None, None
    out["asof"] = ref.isoformat()
    out["missing_required"] = [k for k in ("invoice_number", "due_date", "amount_due") if not out[k]]
    return out


def main():
    ap = argparse.ArgumentParser(description="Extract Mahnwesen fields from a CII/UBL/ZUGFeRD-PDF e-invoice.")
    ap.add_argument("invoice")
    ap.add_argument("--asof", help="reference date YYYY-MM-DD for the Verzug calc")
    args = ap.parse_args()
    try:
        result = parse(args.invoice, args.asof)
    except (ET.ParseError, FileNotFoundError, ValueError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
