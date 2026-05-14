# GDPR / DSGVO data flows

Required for EU enterprise sharing per atypica feedback (Marcus Thorne, Berlin).

For each tool in the stack: **where does live data go**, and **is there a DPA available**.

| Tool | Data residency | Transfers outside EU | DPA |
|---|---|---|---|
| **Claude Code (Anthropic)** | US (default) / EU available | Yes by default | [Anthropic DPA](https://www.anthropic.com/legal/dpa) |
| **Supabase** | EU region (Frankfurt) if configured | No (EU-only project) | [Supabase DPA](https://supabase.com/legal/dpa) |
| **Vercel** | Multi-region edge; data residency depends on project | Yes (US edges) | [Vercel DPA](https://vercel.com/legal/dpa) |
| **Trigger.dev** | <fill> | <fill> | <link> |
| **Notion** | US (default) / EU EEA option for Business+ | Yes | [Notion DPA](https://www.notion.so/notion/Notion-DPA) |
| **Slack** | <fill> | <fill> | <link> |
| **Gmail / Google Workspace** | Multi-region | Yes (US) | [Google DPA](https://workspace.google.com/terms/dpa_terms.html) |
| **Higgsfield** | <fill> | <fill> | <link> |
| **atypica** | <fill> | <fill> | <link> |
| **Gamma** | <fill> | <fill> | <link> |
| **Context7** | <fill> | <fill> | <link> |
| **DSGVO.pro** | EU (own product, Frankfurt) | No | Provided on request |

## What this means in practice

For DSGVO-sensitive workloads (German SME compliance, customer PII):
- Pin Supabase to EU region.
- Avoid sending client PII through Anthropic without DPA in place.
- Consider self-hosted Postgres if data residency is hard requirement.

## What this doesn't replace

This table is **not legal advice**. Consult your DPO. For a one-shot site compliance scan, the `dsgvo-pro` MCP in this stack actually does that — feed it your site URL.
