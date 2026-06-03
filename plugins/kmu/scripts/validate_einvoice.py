#!/usr/bin/env python3
"""Authoritative EN16931 / XRechnung validation of a structured e-invoice.

Wraps the Mustangproject CLI (Apache-2.0) which runs the official EN16931 + XRechnung
Schematron. Mustang needs Java; the fat jar is large (~58 MB) and is NOT committed —
fetch it once with scripts/fetch-mustang.sh (puts it in scripts/vendor/Mustang-CLI.jar).

Usage:
  python3 validate_einvoice.py <invoice.pdf|invoice.xml>

Returns JSON: {status, profile, parsed_pdf, xml_valid, errors:[{id,text}]}.
Exit 0 if status == valid, else 2 (3 if jar/java missing).
"""
import os
import sys
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
JAR = os.path.join(HERE, "vendor", "Mustang-CLI.jar")
JAVA_CANDIDATES = [
    os.environ.get("MUSTANG_JAVA"),
    shutil.which("java"),
    "/opt/homebrew/opt/openjdk/bin/java",
    "/usr/local/opt/openjdk/bin/java",
]


def _java():
    for j in JAVA_CANDIDATES:
        if not j:
            continue
        if os.path.exists(j) or shutil.which(j):
            return j
    return None


def validate(path):
    java = _java()
    if not java:
        return {"status": "unavailable", "reason": "no Java runtime found"}, 3
    if not os.path.exists(JAR):
        return {"status": "unavailable",
                "reason": f"Mustang jar missing — run scripts/fetch-mustang.sh ({JAR})"}, 3
    proc = subprocess.run(
        [java, "-jar", JAR, "--action", "validate", "--source", path, "--disable-file-logging"],
        capture_output=True, text=True,
    )
    # The structured XML report is on stdout; INFO logs go to stderr.
    report = proc.stdout
    out = {"status": "unknown", "profile": None, "parsed_pdf": None,
           "xml_valid": None, "errors": []}
    try:
        start = report.index("<validation")
        root = ET.fromstring(report[start:])
        summ = root.find(".//summary")
        if summ is not None:
            out["status"] = summ.get("status")
        for m in root.findall(".//message"):
            out["errors"].append({"id": m.get("criterion") or m.get("id"),
                                  "text": (m.text or "").strip()})
        xmlnode = root.find(".//xml")
        if xmlnode is not None:
            out["xml_valid"] = xmlnode.get("valid")
        pdfnode = root.find(".//pdf")
        if pdfnode is not None:
            out["parsed_pdf"] = pdfnode.get("valid")
    except (ValueError, ET.ParseError):
        out["status"] = "error"
        out["reason"] = "could not parse Mustang report"
        out["raw_tail"] = report[-500:]
    code = 0 if out["status"] == "valid" else 2
    return out, code


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: validate_einvoice.py <invoice.pdf|invoice.xml>")
    result, code = validate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
