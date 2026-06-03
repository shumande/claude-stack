#!/usr/bin/env python3
"""Generate a DATEV-Format EXTF "Buchungsstapel" CSV for the Steuerberater hand-off.

Verified against TWO independent sources (Phase 0 + adversarial workflow 2026-06-03):
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
import argparse

# --- 125 column names (positions 1..125), reconstructed from the verified layout ---
def _column_names():
    cols = [
        "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz", "Kurs",
        "Basisumsatz", "WKZ Basisumsatz", "Konto", "Gegenkonto (ohne BU-Schlüssel)",
        "BU-Schlüssel", "Belegdatum", "Belegfeld 1", "Belegfeld 2", "Skonto",
        "Buchungstext", "Postensperre", "Diverse Adressnummer", "Geschäftspartnerbank",
        "Sachverhalt", "Zinssperre", "Beleglink",
    ]  # 1..20
    for i in range(1, 9):  # 21..36 Beleginfo Art/Inhalt 1..8 interleaved
        cols += [f"Beleginfo - Art {i}", f"Beleginfo - Inhalt {i}"]
    cols += [  # 37..47
        "KOST1 - Kostenstelle", "KOST2 - Kostenstelle", "Kost-Menge",
        "EU-Land u. USt-IdNr.", "EU-Steuersatz", "Abw. Versteuerungsart",
        "Sachverhalt L+L", "Funktionsergänzung L+L", "BU 49 Hauptfunktionstyp",
        "BU 49 Hauptfunktionsnummer", "BU 49 Funktionsergänzung",
    ]
    for i in range(1, 21):  # 48..87 Zusatzinformation Art/Inhalt 1..20 interleaved
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
    """'YYYY-MM-DD' -> 'DDMM' (year implied by the Wirtschaftsjahr)."""
    y, m, d = iso_date.split("-")
    return f"{d}{m}"


def _amount(value):
    """Unsigned comma-decimal, scale 2. Direction lives in the S/H column."""
    return f"{abs(float(value)):.2f}".replace(".", ",")


def header_fields(p):
    """31 header fields. p carries the batch metadata."""
    f = [""] * 31
    f[0] = "EXTF"
    f[1] = "700"                       # DATEV-Format-Version
    f[2] = "21"                        # Datenkategorie 21 = Buchungsstapel
    f[3] = "Buchungsstapel"
    f[4] = "13"                        # Formatversion of the 125-col layout
    f[5] = p["erzeugt_am"]             # YYYYMMDDHHMMSSmmm (17 digits)
    # f[6] Importiert -> leave empty (DATEV sets it)
    f[7] = p.get("herkunft", "AF")     # 2-char origin tag
    f[8] = p.get("exportiert_von", "")
    # f[9] Importiert von -> empty
    f[10] = str(p["berater"])
    f[11] = str(p["mandant"])
    f[12] = p["wj_beginn"]             # YYYYMMDD
    f[13] = str(p.get("sachkontenlaenge", 4))
    f[14] = p["datum_von"]             # YYYYMMDD
    f[15] = p["datum_bis"]             # YYYYMMDD
    f[16] = p.get("bezeichnung", "")
    # f[17] Diktatkürzel empty
    f[18] = str(p.get("buchungstyp", 1))
    # f[19] Rechnungslegungszweck empty
    f[20] = str(p.get("festschreibung", 0))
    f[21] = p.get("wkz", "EUR")
    # f[22..30] reserved -> empty
    return f


def booking_fields(b, sachkontenlaenge=4):
    """125 data fields for one booking."""
    f = [""] * N_COLS
    f[0] = _amount(b["umsatz"])                       # 1 Umsatz (unsigned)
    f[1] = b["soll_haben"]                            # 2 S / H
    # 3 WKZ Umsatz -> empty (uses header WKZ); 4-6 empty
    f[6] = str(b["konto"]).rjust(sachkontenlaenge, "0")        # 7 Konto
    f[7] = str(b["gegenkonto"]).rjust(sachkontenlaenge, "0")   # 8 Gegenkonto
    f[8] = b.get("bu_schluessel", "")                 # 9 BU-Schlüssel
    f[9] = _ddmm(b["belegdatum"])                     # 10 Belegdatum DDMM
    f[10] = b.get("belegfeld1", "")                   # 11 Belegfeld 1 (Rechnungsnr / OP-key)
    # 12 Belegfeld 2, 13 Skonto -> empty
    f[13] = b.get("buchungstext", "")                 # 14 Buchungstext
    return f


# string columns get quoted; everything else is unquoted. Indices are 0-based.
_HEADER_STRING_IDX = {0, 3, 7, 8, 16, 21}
_BOOKING_STRING_IDX = {1, 2, 5, 8, 10, 11, 13}  # S/H, WKZ, BU, Belegfeld1/2, Buchungstext...


def _render_line(fields, string_idx):
    out = []
    for i, val in enumerate(fields):
        s = "" if val is None else str(val)
        if i in string_idx and s != "":
            out.append('"' + s.replace('"', '""') + '"')
        else:
            out.append(s)  # numerics/dates and empty strings: bare
    return ";".join(out)


def build(bookings, header_params):
    sk = header_params.get("sachkontenlaenge", 4)
    lines = [
        _render_line(header_fields(header_params), _HEADER_STRING_IDX),
        _render_line(COLUMN_NAMES, set(range(N_COLS))),  # column-name row: all quoted
        *[_render_line(booking_fields(b, sk), _BOOKING_STRING_IDX) for b in bookings],
    ]
    # sanity: header 31 fields, every other line 125 fields
    assert lines[0].count(";") == 30, lines[0].count(";")
    for ln in lines[1:]:
        assert ln.count(";") == N_COLS - 1, ln.count(";")
    return "\r\n".join(lines) + "\r\n"


def write_file(path, bookings, header_params):
    data = build(bookings, header_params)
    with open(path, "wb") as fh:
        fh.write(data.encode("cp1252", errors="replace"))
    return path


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
    if args.out == "-":
        sys.stdout.write(build(bookings, _demo_params()))
    else:
        write_file(args.out, bookings, _demo_params())
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
