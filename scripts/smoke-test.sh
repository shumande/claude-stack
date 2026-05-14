#!/usr/bin/env bash
# smoke-test.sh — Verify every MCP server in .mcp.json actually responds.
# Returns 0 if all green, 1 if any failure.
# Designed to catch the "fake-green" trap: process running but not responding.
#
# Portable: macOS (no GNU coreutils required) + Linux (Ubuntu/CI).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_JSON="$REPO_ROOT/.mcp.json"
ENV_FILE="$REPO_ROOT/.env"

if [[ ! -f "$MCP_JSON" ]]; then
  echo "ERROR: .mcp.json not found at $MCP_JSON" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "WARN: .env not found — stdio servers may fail (missing credentials)" >&2
fi

# Load env vars if .env exists
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# Check required tools
for tool in jq curl; do
  if ! command -v "$tool" &>/dev/null; then
    echo "ERROR: $tool not found in PATH" >&2
    exit 1
  fi
done

# ---------------------------------------------------------------------------
# Portable timeout: prefer GNU timeout (Linux), then gtimeout (macOS+brew),
# then fall back to a pure-bash background-process approach.
# Usage: portable_timeout <seconds> <cmd> [args...]
# ---------------------------------------------------------------------------
_TIMEOUT_CMD=""
if command -v timeout &>/dev/null; then
  _TIMEOUT_CMD="timeout"
elif command -v gtimeout &>/dev/null; then
  _TIMEOUT_CMD="gtimeout"
fi

portable_timeout() {
  local secs="$1"; shift
  if [[ -n "$_TIMEOUT_CMD" ]]; then
    "$_TIMEOUT_CMD" "$secs" "$@"
    return $?
  fi
  # Pure-bash fallback: run in background, kill after $secs seconds
  "$@" &
  local pid=$!
  (
    sleep "$secs"
    kill "$pid" 2>/dev/null
  ) &
  local watchdog=$!
  wait "$pid" 2>/dev/null
  local rc=$?
  kill "$watchdog" 2>/dev/null
  wait "$watchdog" 2>/dev/null || true
  return $rc
}

# ---------------------------------------------------------------------------
# Test each MCP server
# ---------------------------------------------------------------------------
SERVERS=$(jq -r '.mcpServers | keys[]' "$MCP_JSON")
FAIL=0
PASS=0

MCP_INIT_REQUEST='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke-test","version":"0.0.1"}}}'

for server in $SERVERS; do
  TYPE=$(jq -r ".mcpServers.\"$server\".type // \"stdio\"" "$MCP_JSON")

  if [[ "$TYPE" == "http" ]]; then
    URL=$(jq -r ".mcpServers.\"$server\".url" "$MCP_JSON")

    # MCP initialize handshake over HTTP
    # The `|| echo "000"` ensures set -e doesn't abort on curl network error
    HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" \
      -X POST "$URL" \
      -H "Content-Type: application/json" \
      -H "MCP-Protocol-Version: 2024-11-05" \
      -d "$MCP_INIT_REQUEST" \
      --max-time 10 || echo "000")

    if [[ "$HTTP_CODE" =~ ^(200|202)$ ]]; then
      echo "✓ $server (http, $HTTP_CODE)"
      PASS=$((PASS+1))
    else
      echo "✗ $server (http, $HTTP_CODE) — endpoint not responding"
      FAIL=$((FAIL+1))
    fi

  else
    # stdio server — launch it, pipe initialize request, capture first JSON line.
    #
    # $CMD $ARGS uses intentional word-splitting so that commands like
    # `npx -y @pkg@version` are split into proper argv elements.
    # Caveat: paths with spaces in CMD would break — acceptable for v1 since
    # all known MCP servers use `npx` which has no spaces.
    #
    # Race note (v1 known limitation): the server may still be initializing
    # when we send the request; `head -1` captures the first line of stdout.
    # For well-behaved stdio MCP servers this is fine — they process stdin
    # synchronously and emit the initialize response before any other output.

    CMD=$(jq -r ".mcpServers.\"$server\".command" "$MCP_JSON")
    # Build args string via jq; empty if no args array
    ARGS=$(jq -r ".mcpServers.\"$server\".args[]?" "$MCP_JSON" | tr '\n' ' ')

    # Capture stdout to a temp file to avoid SIGPIPE/pipefail interaction.
    # When head -1 exits after reading one line, the left side of a pipeline
    # receives SIGPIPE (exit 141). Under set -euo pipefail this would trigger
    # the || echo "" fallback even when the server DID respond correctly.
    # Using a temp file decouples the two operations cleanly.
    _TMPFILE=$(mktemp)
    portable_timeout 30 $CMD $ARGS < <(echo "$MCP_INIT_REQUEST") > "$_TMPFILE" 2>/dev/null || true
    RESPONSE=$(head -1 "$_TMPFILE" 2>/dev/null || echo "")
    rm -f "$_TMPFILE"

    if [[ "$RESPONSE" == *'"protocolVersion"'* ]]; then
      echo "✓ $server (stdio)"
      PASS=$((PASS+1))
    else
      echo "✗ $server (stdio) — no protocolVersion in response"
      FAIL=$((FAIL+1))
    fi
  fi
done

echo ""
echo "Result: $PASS passed, $FAIL failed"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
exit 0
