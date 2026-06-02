---
name: ki-vo-classify
description: Classify an AI system under the EU AI Act (KI-VO) into prohibited, high-risk, limited-risk/transparency, or minimal risk, and list the resulting duties. Use when someone asks whether their AI use is allowed, what obligations their chatbot or AI feature has under the AI Act / KI-VO, or how their system is classified. Grounds every tier in the live article text via the dsgvo.pro MCP. Works without an API key.
argument-hint: "<description of the AI system and how it's used>"
---

# KI-VO / EU AI Act Classification

> Connectors and tools: [CONNECTORS.md](../../CONNECTORS.md). Uses the free
> `get-article` / `search-law` tools — no API key needed.

Classify an AI system under the **KI-Verordnung (EU) 2024/1689 (AI Act)** and
state the duties that follow. The Act is risk-tiered: the same model is fine in
one use and forbidden in another, so classification is about the **use**, not
the technology. This is highly relevant for small businesses deploying chatbots,
content generators, and lead-scoring — the duties that bite most are the
**transparency** ones in Art. 50.

## Trigger

User asks "is my AI allowed / erlaubt", "what does the AI Act / KI-VO require for
my chatbot", "classify my AI system", "muss ich kennzeichnen, dass das KI ist",
or describes an AI feature and wants its obligations.

## Inputs

Get enough to judge the **use**, not just the tech:

1. **What the system does** and the concrete use case
2. **Who it affects** and in what context (workplace, hiring, credit, education,
   law enforcement, public spaces, consumers)
3. **Whether it interacts with people directly** (chatbot, voice agent)
4. **Whether it generates or manipulates content** (text, image, audio, video)
5. **Whether it does** emotion recognition, biometric categorization, scoring,
   or profiling

## Grounding step (do this first)

Fetch the tier definitions before classifying — quote, don't recall:

- `get-article` **KI-VO Art. 5** — prohibited practices (unacceptable risk).
- `get-article` **KI-VO Art. 6** — high-risk classification rules (note it
  refers to Anhang I and Anhang III for the actual high-risk use cases).
- `get-article` **KI-VO Art. 50** — transparency duties (direct interaction
  disclosure, synthetic-content marking, deepfake and AI-text disclosure).
- Use `search-law` (law `ki-vo`) for anything else in scope.

## Classification (apply in order)

1. **Prohibited (Art. 5)?** — manipulative/subliminal techniques causing harm,
   exploiting vulnerabilities, social scoring, untargeted facial-image scraping,
   emotion recognition at work/school, certain biometric categorization, most
   real-time remote biometric ID in public. If yes → **stop: not allowed.**
2. **High-risk (Art. 6 + Anhang III)?** — safety component of a regulated
   product, or an Anhang III use (employment/HR, education, credit/insurance
   scoring, essential services, law enforcement, migration, biometrics, critical
   infrastructure). Note the Art. 6(3) carve-out for narrow procedural tasks,
   and that profiling of natural persons keeps it high-risk. If yes → heavy
   provider/deployer duties (risk management, data governance, logging, human
   oversight, conformity assessment, registration).
3. **Transparency / limited risk (Art. 50)?** — interacts with people (chatbot
   → must disclose it's AI), or generates/manipulates content (synthetic media
   must be machine-marked; deepfakes and AI text on matters of public interest
   must be disclosed). Most SMB uses land here.
4. **Minimal risk** — everything else; no specific KI-VO duty, voluntary codes
   encouraged.

Also flag **GPAI** (general-purpose models) provider duties only if the user is
a model provider, not just a deployer.

## Output (in German)

```
# KI-VO-Einstufung: <System>

## Einstufung
**<Verboten / Hochrisiko / Transparenzpflicht / Minimales Risiko>**
<1–2 Sätze Begründung, bezogen auf die Nutzung>

## Begründung je Stufe
| Stufe | Trifft zu? | Rechtsgrundlage | Warum |
|-------|-----------|-----------------|-------|
| Verboten | nein | Art. 5 KI-VO (Zitat) | … |
| Hochrisiko | nein | Art. 6 KI-VO + Anhang III (Zitat) | … |
| Transparenz | JA | Art. 50 KI-VO (Zitat) | Chatbot → Offenlegungspflicht |

## Pflichten
<konkrete, umsetzbare Liste für die zutreffende Stufe>

## Fristen
<relevante Geltungsdaten der KI-VO, sofern aus dem Gesetzestext belegbar>
```

Each "Rechtsgrundlage" must quote text returned by `get-article`. For high-risk,
say explicitly that the concrete use cases live in **Anhang III** and that the
list must be checked there — don't assert membership from memory.

## After

Offer to: detail the duties for the assigned tier, draft the Art. 50 disclosure
wording (e.g. a chatbot "Sie chatten mit einem KI-Assistenten" notice), or check
whether personal-data use also triggers DSGVO duties (`datenschutz-review`).

## Boundaries

Decision-support, not legal advice — say so once. KI-VO classification,
especially the high-risk line and Anhang III membership, is genuinely contested
and the Commission guidance is still arriving; flag close calls and recommend a
specialist lawyer rather than asserting certainty. Do not invent application
dates or Anhang III entries — if it isn't in the fetched text, say so.
