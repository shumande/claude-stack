# Failure modes

Real ways this stack breaks, with concrete fixes. If you hit something not listed — open an issue.

---

## STDIO corruption from `console.log`

**Symptom:** MCP server appears connected but Claude reports no tools / garbled JSON.

**Cause:** Any `console.log` inside an MCP server that uses STDIO transport writes to stdout — the same channel MCP uses for JSON-RPC. The output corrupts the protocol stream.

**Fix:** Replace `console.log` with `console.error` (stderr is safe) or use a proper logger that writes to a file. Audit all MCP-server dependencies for stray `console.log`.

---

## Windows MSIX path corruption (Error 32000)

**Symptom:** Claude Code fails to launch MCP servers; error mentions Error 32000 or invalid path.

**Cause:** Spaces in Windows paths (e.g. `C:\Program Files\...`) aren't quoted by some MCP launchers. Combined with MSIX-installed Node versions placing binaries in deep nested paths, the launcher truncates at the first space.

**Fix:** Either install Node via `nvm-windows` outside Program Files, or escape paths in `.mcp.json` env (`"PATH": "\"C:\\Program Files\\...\""` style). For new installs, prefer WSL2 over native Windows when possible.

---

## Zombie MCP processes

**Symptom:** After closing Claude Code, `ps aux | grep mcp` shows still-running processes. Memory leak over a session.

**Cause:** Some MCP servers don't register a SIGTERM handler. When the parent (Claude Code) exits, child stays alive.

**Fix:** Add a wrapper in `.mcp.json`:

```json
{
  "command": "bash",
  "args": ["-c", "trap 'kill $!' SIGTERM; <original-command> & wait"]
}
```

Or, as a daily ritual, run `pkill -f mcp-server` before starting Claude.

---

## `~/.claude/settings.json` vs `~/.claude.json` conflict

**Symptom:** Settings appear to apply inconsistently between sessions. `permissions.deny` works in one project, not another.

**Cause:** Claude Code reads two locations: `~/.claude/settings.json` (newer) and `~/.claude.json` (legacy). If both exist with overlapping keys, behavior depends on order of precedence which has changed across releases.

**Fix:** Keep only `~/.claude/settings.json`. Migrate any `~/.claude.json` contents into it and delete the legacy file. Check: `ls -la ~/.claude*`.

---

<!-- Operator: add 3+ more failure modes from your own experience before launch. -->
