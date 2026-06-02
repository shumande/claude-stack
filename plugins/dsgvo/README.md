# DSGVO Compliance — Claude plugin

German digital-law compliance for websites, as a Claude Code / Cowork plugin.
Scan a site, review your **Datenschutzerklärung**, check your **cookie consent**
and **Impressum**, and classify **AI systems** under the AI Act — grounded in
DSGVO, BDSG, TDDDG, DDG and KI-VO.

## Why this exists

Anthropic's `legal` plugin is built for US law. This is the European edition of
that idea, narrowed to the one task German businesses actually get fined for:
website data protection. It is **not a translation** — the workflows are built
around German law, and every legal citation is pulled **live** from the
[dsgvo.pro](https://dsgvo.pro) MCP server. The model does not quote paragraph
numbers from memory, so it can't invent a §25 that says something it doesn't.
That grounding is the whole point.

## Skills

| Skill | What it does | API key? |
|-------|--------------|----------|
| `website-scan` | Runs a live scan of a URL, prioritizes findings by Abmahnung risk, cites each to the exact paragraph | **yes** (free tier 3/mo) |
| `datenschutz-review` | Reviews or drafts a Datenschutzerklärung against Art. 13/14 DSGVO | no |
| `cookie-consent` | Checks the cookie banner/flow against § 25 TDDDG and consent dark patterns | no |
| `impressum` | Checks the Impressum against the § 5 DDG information duties + placement | no |
| `ki-vo-classify` | Classifies an AI system under the AI Act (KI-VO) — prohibited / high-risk / transparency / minimal — and lists the duties | no |

Output is written in German (it's for German owners and their lawyers); the
skill instructions are in English so the repo stays readable.

## Install

```bash
claude plugin marketplace add shumande/claude-stack
claude plugin install dsgvo@claude-stack
```

Then just ask, e.g.:

- "Prüfe meine Datenschutzerklärung" + paste it
- "Cookie-Banner von example.de prüfen"
- "Scan example.de auf DSGVO" (needs an API key — see below)

## API key

Four of the five skills work immediately with no key, because the dsgvo.pro
tools `search-law` and `get-article` are free. Only `website-scan` needs a key,
because it runs a real browser scan. Get one at
https://dsgvo.pro/api-keys and follow [CONNECTORS.md](./CONNECTORS.md). Your key
stays in your local config — it is never part of this repo.

## Not legal advice

This is decision-support. Have a Datenschutzbeauftragter or lawyer confirm
anything you rely on — especially consent design, third-country transfers, and
whether a DSFA is required.

## License

MIT.
