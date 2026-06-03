#!/usr/bin/env python3
"""Generate a DATEV-Format EXTF "Buchungsstapel" CSV for the Steuerberater hand-off.

Verified against TWO independent sources (adversarial workflow 2026-06-03):
  1. the ledermann/datev open-source gem (ran it; header + data byte-identical to its
     shipped examples/EXTF_Buchungsstapel.csv),
  2. DATEV's official ASCII-Dateibeschreibung Dok.-Nr. 1003221.

Invariants (load-bearing — do not change without re-verifying):
  - File = 3 sections: header line (31 fields) + column-name line (125) + data rows (125 each).
  - Encoding Windows-1252 (cp1252), NO BOM. Line terminator CRLF, including after last row.
  - Field delimiter ";". Strings quoted with `"`, internal `"` doubled; empty string = bare.
  - Numerics/dates/booleans unquoted. Decimals use comma, scale 2, UNSIGNED
    (direction is the separate Soll/Haben column).
  - Belegdatum = DDMM (year implied by the header Wirtschaftsjahr).
  - Konto/Gegenkonto zero-left-padded to the header Sachkontenlänge.

This writes the file; it does NOT validate the bookings' accounting correctness.
"""
import sys
import csv
import io
import json
import math
import argparse
import datetime


def _column_names():
    cols = [
        "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz", "Kurs",
        "Basisumsatz", "WKZ Basisumsatz", "Konto", "Gegenkonto (ohne BU-Schlüssel)",
        "BU-Schlüssel", "Belegdatum", "Belegfeld 1", "Belegfeld 2", "Skonto",
        "Buchungstext", "Postensperre", "Diverse Adressnummer", "Geschäftspartnerbank",
        "Sachverhalt", "Zinssperre", "Beleglink",
    ]  # 1..20
    for i in range(1, 9):  # 21..36
        cols += [f"Beleginfo - Art {i}", f"Beleginfo - Inhalt {i}"]
    cols += [  # 37..47
        "KOST1 - Kostenstelle", "KOST2 - Kostenstelle", "Kost-Menge",
        "EU-Land u. USt-IdNr.", "EU-Steuersatz", "Abw. Versteuerungsart",
        "Sachverhalt L+L", "Funktionsergänzung L+L", "BU 49 Hauptfunktionstyp",
        "BU 49 Hauptfunktionsnummer", "BU 49 Funktionsergänzung",
    ]
    for i in range(1, 21):  # 48..87
        cols += [f"Zusatzinformation - Art {i}", f"Zusatzinformation - Inhalt {i}"]
    cols += [  # 88..125
        "Stück", "Gewicht", "Zahlweise", "Forderungsart", "Veranlagungsjahr",
        "Zugeordnete Fälligkeit", "Skontotyp", "Auftragsnummer", "Buchungstyp",
        "USt-Schlüssel (Anzahlungen)", "EU-Mitgliedstaat (Anzahlungen)",
        "Sachverhalt L+L (Anzahlungen)", "EU-Steuersatz (Anzahlungen)",
        "Erlöskonto (Anzahlungen)", "Herkunft-Kz", "Leerfeld", "KOST-Datum",
        "SEPA-Mandatsreferenz", "Skontosperre", "Gesellschaftername",
        "Beteiligtennummer", "Identifikationsnummer", "Zeichnernummer",
        "Postensperre bis", "Bezeichnung", "Kennzeichen", "Festschreibung",
        "Leistungsdatum", "Datum Zuord.", "Fälligkeit", "Generalumkehr (GU)",
        "Steuersatz", "Land", "Abrechnungsreferenz", "BVV-Position",
        "EU-Mitgliedstaat u. USt-IdNr. (Ursprung)", "EU-Steuersatz (Ursprung)",
        "Abw. Skontokonto",
    ]
    assert len(cols) == 125, f"column count {len(cols)} != 125"
    return cols

COLUMN_NAMES = _column_names()
N_COLS = 125


def _ddmm(iso_date):
    y, m, d = iso_date.split("-")
    return f"{d}{m}"


def _amount(value):
    """Unsigned comma-decimal, scale 2. Rejects non-finite values loudly."""
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"Non-finite Umsatz: {value!r}")
    return f"{abs(v):.2f}".replace(".", ",")


def _no_newline(s, field):
    """A bare CR/LF inside a string field would split the DATEV row. Reject it."""
    if any(c in s for c in "\r\n"):
        raise ValueError(f"Field {field!r} contains a newline — not allowed in EXTF: {s!r}")
    return s


def header_fields(p):
    f = [""] * 31
    f[0] = "EXTF"
    f[1] = "700"
    f[2] = "21"
    f[3] = "Buchungsstapel"
    f[4] = "13"
    f[5] = p["erzeugt_am"]
    f[7] = p.get("herkunft", "AF")
    f[8] = p.get("exportiert_von", "")
    f[10] = str(p["berater"])
    f[11] = str(p["mandant"])
    f[12] = p["wj_beginn"]
    f[13] = str(p.get("sachkontenlaenge", 4))
    f[14] = p["datum_von"]
    f[15] = p["datum_bis"]
    f[16] = p.get("bezeichnung", "")
    f[18] = str(p.get("buchungstyp", 1))
    f[20] = str(p.get("festschreibung", 0))
    f[21] = p.get("wkz", "EUR")
    return f


def booking_fields(b, sachkontenlaenge=4):
    f = [""] * N_COLS
    f[0] = _amount(b["umsatz"])                                 # 1 Umsatz (unsigned)
    f[1] = b["soll_haben"]                                      # 2 S / H
    f[6] = _account(b["konto"], sachkontenlaenge)              # 7 Konto
    f[7] = _account(b["gegenkonto"], sachkontenlaenge)         # 8 Gegenkonto
    f[8] = b.get("bu_schluessel", "")                          # 9 BU-Schlüssel
    f[9] = _ddmm(b["belegdatum"])                              # 10 Belegdatum DDMM
    f[10] = _no_newline(b.get("belegfeld1", ""), "Belegfeld1") # 11 Belegfeld 1
    f[13] = _no_newline(b.get("buchungstext", ""), "Buchungstext")  # 14 Buchungstext
    return f


def _account(value, sachkontenlaenge):
    """Zero-pad to Sachkontenlänge. Personenkonten may be exactly 1 digit longer."""
    s = str(value)
    if len(s) > sachkontenlaenge + 1:
        raise ValueError(
            f"Konto {value!r} has {len(s)} digits; max is Sachkontenlänge+1 "
            f"({sachkontenlaenge + 1}) for personal accounts")
    return s.rjust(sachkontenlaenge, "0")


_HEADER_STRING_IDX = {0, 3, 7, 8, 16, 21}
_BOOKING_STRING_IDX = {1, 2, 5, 8, 10, 11, 13}


def _render_line(fields, string_idx):
    out = []
    for i, val in enumerate(fields):
        s = "" if val is None else str(val)
        if i in string_idx and s != "":
            out.append('"' + s.replace('"', '""') + '"')
        else:
            out.append(s)
    return ";".join(out)


def _assert_field_count(line, expected):
    """RFC-4180-aware count (quoted ';' must not inflate the count)."""
    row = next(csv.reader(io.StringIO(line), delimiter=";", quotechar='"'))
    if len(row) != expected:
        raise AssertionError(f"rendered {len(row)} fields, expected {expected}: {line[:80]}…")


def build(bookings, header_params):
    sk = header_params.get("sachkontenlaenge", 4)
    lines = [
        _render_line(header_fields(header_params), _HEADER_STRING_IDX),
        _render_line(COLUMN_NAMES, set(range(N_COLS))),
        *[_render_line(booking_fields(b, sk), _BOOKING_STRING_IDX) for b in bookings],
    ]
    _assert_field_count(lines[0], 31)
    for ln in lines[1:]:
        _assert_field_count(ln, N_COLS)
    return "\r\n".join(lines) + "\r\n"


def _cp1252_ok(ch):
    try:
        ch.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False


def write_file(path, bookings, header_params):
    data = build(bookings, header_params)
    try:
        encoded = data.encode("cp1252")
    except UnicodeEncodeError:
        # DATEV semantics: non-cp1252 chars become a space (matches ledermann replace:' ').
        # Done per-char so the rest stays intact, and warn which chars were dropped.
        bad = sorted({ch for ch in data if not _cp1252_ok(ch)})
        sys.stderr.write(f"WARNING: {len(bad)} non-cp1252 char(s) replaced with space: {bad}\n")
        encoded = "".join(ch if _cp1252_ok(ch) else " " for ch in data).encode("cp1252")
    with open(path, "wb") as fh:
        fh.write(encoded)
    return path


_REQUIRED_PARAMS = ("berater", "mandant", "wj_beginn", "datum_von", "datum_bis")


def resolve_params(args):
    if args.params:
        with open(args.params, encoding="utf-8") as fh:
            p = json.load(fh)
    elif any(getattr(args, k) is not None for k in _REQUIRED_PARAMS):
        p = {k: getattr(args, k) for k in _REQUIRED_PARAMS if getattr(args, k) is not None}
        p["bezeichnung"] = args.bezeichnung or ""
    else:
        sys.stderr.write("WARNING: using DEMO header params (Berater 1001 / Mandant 456) — "
                         "NOT valid for a real client file. Pass --params or --berater/--mandant/etc.\n")
        p = _demo_params()
    missing = [k for k in _REQUIRED_PARAMS if not p.get(k)]
    if missing:
        sys.exit(f"missing required header params: {', '.join(missing)}")
    p.setdefault("erzeugt_am", datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "000")
    return p


def _demo_params():
    return {
        "erzeugt_am": "20260603120000000", "berater": 1001, "mandant": 456,
        "wj_beginn": "20260101", "sachkontenlaenge": 4, "datum_von": "20260401",
        "datum_bis": "20260430", "bezeichnung": "KMU-Hand-off", "wkz": "EUR",
        "exportiert_von": "ai-firma", "herkunft": "AF",
    }


def main():
    ap = argparse.ArgumentParser(description="Generate a DATEV-EXTF Buchungsstapel.")
    ap.add_argument("--bookings", help="JSON file: list of booking dicts. Omit for a demo row.")
    ap.add_argument("--params", help="JSON file with header params (berater, mandant, wj_beginn, datum_von, datum_bis, ...).")
    ap.add_argument("--berater", help="Beraternummer")
    ap.add_argument("--mandant", help="Mandantennummer")
    ap.add_argument("--wj-beginn", dest="wj_beginn", help="Wirtschaftsjahr-Beginn YYYYMMDD")
    ap.add_argument("--datum-von", dest="datum_von", help="Stapel-Zeitraum von YYYYMMDD")
    ap.add_argument("--datum-bis", dest="datum_bis", help="Stapel-Zeitraum bis YYYYMMDD")
    ap.add_argument("--bezeichnung", help="Stapel-Bezeichnung")
    ap.add_argument("-o", "--out", default="-", help="output .csv path, or - for stdout text")
    args = ap.parse_args()

    if args.bookings:
        with open(args.bookings, encoding="utf-8") as fh:
            bookings = json.load(fh)
    else:
        bookings = [{
            "umsatz": 24.95, "soll_haben": "H", "konto": 1200, "gegenkonto": 4940,
            "bu_schluessel": "8", "belegdatum": "2026-02-21", "belegfeld1": "",
            "buchungstext": "Fachbuch: Controlling für Dummies",
        }]
    params = resolve_params(args)
    if args.out == "-":
        sys.stdout.write(build(bookings, params))
    else:
        write_file(args.out, bookings, params)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
