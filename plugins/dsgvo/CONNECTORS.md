# Connectors

This plugin is powered by a single connector: the **dsgvo.pro MCP server**. It
is what makes the plugin different from a generic "German GDPR" prompt — every
law reference in the output is fetched live from a real legal database instead
of recalled from the model's memory, so paragraph numbers are correct and not
hallucinated.

## dsgvo.pro MCP

Pre-configured in [`.mcp.json`](./.mcp.json):

```json
{ "mcpServers": { "dsgvo-pro": { "type": "http", "url": "https://dsgvo.pro/api/mcp" } } }
```

It exposes these tools:

| Tool | Auth | Used by |
|------|------|---------|
| `search-law` | free, no key | datenschutz-review, cookie-consent, website-scan |
| `get-article` | free, no key | all skills (exact article/paragraph text for citations) |
| `list-laws` | free, no key | all skills |
| `check-compliance` | **API key required** | website-scan |
| `get-scan-status` / `get-scan-result` | public per scanId | website-scan |

Covered laws: DSGVO (GDPR), BDSG, TDDDG, DDG, KI-VO (EU AI Act), BFSG.

## API key — what works without one, what needs one

**Works immediately, no key:** `datenschutz-review` and `cookie-consent`. They
only use the free `search-law` / `get-article` tools.

**Needs your own key:** `website-scan`, because it runs a live browser scan via
`check-compliance` (this costs the dsgvo.pro service money). Free tier is 3
scans/month.

To enable scans:

1. Get a key at https://dsgvo.pro/api-keys (format `dsp_live_...`).
2. Add an auth header to this plugin's `.mcp.json`:

   ```json
   {
     "mcpServers": {
       "dsgvo-pro": {
         "type": "http",
         "url": "https://dsgvo.pro/api/mcp",
         "headers": { "Authorization": "Bearer dsp_live_YOUR_KEY" }
       }
     }
   }
   ```

3. Restart Claude Code so the connector reloads.

Never commit your key. If you call `check-compliance` without one you get a
clear error (`-32001`) with these same instructions — no silent failure.
