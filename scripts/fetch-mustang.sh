#!/usr/bin/env bash
# Fetch the Mustangproject CLI fat jar (Apache-2.0) for authoritative EN16931/XRechnung
# validation. ~58 MB, NOT committed to git. Run once.
set -euo pipefail
cd "$(dirname "$0")/.."
VER="${1:-2.23.1}"
DEST="plugins/kmu/scripts/vendor/Mustang-CLI.jar"
URL="https://repo1.maven.org/maven2/org/mustangproject/Mustang-CLI/${VER}/Mustang-CLI-${VER}.jar"
mkdir -p "$(dirname "$DEST")"
echo "Fetching Mustang-CLI ${VER} ..."
curl -fSL --retry 3 -o "$DEST" "$URL"
echo "Wrote $DEST ($(du -h "$DEST" | cut -f1))"
JAVA="${MUSTANG_JAVA:-$(command -v java || echo /opt/homebrew/opt/openjdk/bin/java)}"
"$JAVA" -jar "$DEST" --help >/dev/null 2>&1 && echo "OK: jar runs" || echo "WARN: jar present but java check failed — ensure a JRE is installed"
