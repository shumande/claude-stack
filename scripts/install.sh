#!/usr/bin/env bash
# install.sh — Idempotent setup of Claude Code with this MCP stack.
# Safe to re-run. Detects macOS / Linux / Windows-WSL.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "→ Setting up Claude-Stack baseline in $REPO_ROOT"

# 1. .env from template
if [[ ! -f "$REPO_ROOT/.env" ]]; then
  cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
  echo "  Created .env from .env.example — fill in your tokens before running smoke-test"
else
  echo "  .env exists — skipping"
fi

# 2. .claude/settings.local.json from example
mkdir -p "$REPO_ROOT/.claude"
if [[ ! -f "$REPO_ROOT/.claude/settings.local.json" ]]; then
  cp "$REPO_ROOT/settings.example.json" "$REPO_ROOT/.claude/settings.local.json"
  echo "  Created .claude/settings.local.json from settings.example.json"
else
  echo "  .claude/settings.local.json exists — skipping"
fi

# 3. Detect OS
OS="$(uname -s)"
case "$OS" in
  Darwin)
    echo "  OS: macOS detected"
    ;;
  Linux)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      echo "  OS: WSL detected — note Windows config paths in docs/failure-modes.md"
    else
      echo "  OS: Linux detected"
    fi
    ;;
  *)
    echo "  WARN: untested OS: $OS"
    ;;
esac

# 4. Required tools
echo "→ Checking required tools"
for tool in node npm jq curl git; do
  if command -v "$tool" &>/dev/null; then
    VERSION=$("$tool" --version 2>&1 | head -1)
    echo "  ✓ $tool — $VERSION"
  else
    echo "  ✗ $tool — NOT INSTALLED (required)"
    exit 1
  fi
done

# 5. Next steps
echo ""
echo "→ Setup complete. Next steps:"
echo "  1. Fill in tokens in .env (see comments)"
echo "  2. Run: bash scripts/smoke-test.sh"
echo "  3. Start Claude Code in this directory: claude"
