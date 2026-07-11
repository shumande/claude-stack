---
name: agent-council
description: >
  Гоняй артефакт (сценарий, текст, находки) через СОВЕТ разных ИИ и получай
  сведённый финал. Гетерогенный конвейер: 5 мозгов (Claude/GPT/Gemini/Kimi/GLM)
  параллельно отдают компактный verdict-JSON, Claude синтезирует. Триггеры:
  «грейд советом», «прогони через совет моделей», «мульти-ИИ оценка», перенос
  триады kors на конвейер. НЕ для одноразового вопроса одной модели.
---

# agent-council — совет разных ИИ как конвейер

Форма: `[вход] → [СОВЕТ: 5 моделей ‖] → [синтез Claude] → [финал]`. Хаба/шины нет —
оркестрирует скрипт, между агентами летит тугой JSON, наружу только финал.
Дизайн: `~/Projects/docs/superpowers/specs/2026-07-11-multi-ai-agent-conveyor-design.md`.

## Запуск (любое окно, по пути — перезагрузка не нужна)

```bash
OPENROUTER_API_KEY=sk-or-...  python3 ~/.claude/skills/agent-council/council.py \
  --task @rubric.txt  --file scenario.txt  --out ./_council_run
# или артефакт на stdin:
cat scenario.txt | OPENROUTER_API_KEY=sk-or-... python3 ~/.claude/skills/agent-council/council.py \
  --task "оцени хук рилса, что резать"
```

- `--voices claude,gpt,gemini` — подмножество (напр. только $0-голоса).
- `--out <dir>` — сохранит `verdicts.json` (сырые вердикты), `final.md`, `stats.json` (провод в байтах/токенах).
- Финал печатается в stdout; прогресс совета — в stderr.

## Ключи / что на чём едет (проверено живьём 11.07.2026)

| Голос | Механизм | $ | Ключ |
|---|---|---|---|
| claude | `claude -p` (Claude Code headless) | $0 подписка | — |
| gpt | `~/.local/bin/codex-grade` (gpt-5.5) | $0 ChatGPT-подписка | — |
| gemini | `agy` Gemini 3.1 Pro (High); >12k промпт → OpenRouter фолбэк | $0 Google-подписка | — |
| kimi | moonshot curl, kimi-k2.6, temp=1, max_tokens 16k | центы | `MOONSHOT_API_KEY` (env) |
| glm | OpenRouter `z-ai/glm-5.2` | центы | `OPENROUTER_API_KEY` |

**Правило ключей:** `OPENROUTER_API_KEY` — свой на проект (память `reference_openrouter_keys_per_project`);
не тащить чужой. Для kors — kors-ключ; смок делался ключом kliver как временный.
PII клиентов через OpenRouter НЕ гнать (US-инфра) — совет для СВОИХ артефактов.

## Протокол (контракт между агентами)

Ключи ТОЛЬКО ASCII (грабля StructuredOutput). Проза — лишь в финале синтеза.
```json
{"from":"kimi","verdict":"weak","severity":2,
 "cuts":[{"at":"хук","why":"..."}],"root":"...","graft":["..."]}
```
Если модель не отдала валидный JSON — её выход кладётся сырым (`parse_error`), синтез всё равно видит.

## Грабли (из reference_kors_triada_models)
- Kimi думает долго → `--max-time 900`, контент может уйти в `reasoning_content`.
- agy виснет на промпте >13k → скрипт сам уходит в OpenRouter-фолбэк.
- codex: `read-only`+`ephemeral` уже в шиме; модель текста = `gpt-5.5`, не sol/terra.
- версии моделей ПРОТУХАЮТ — сверять slug перед привязкой (GLM-5.2 подтверждён 11.07).

## Каждый прогон → фидбек в скилл
Кривой вердикт/адаптер молчит — правь `council.py`, не терпи (канон skills).
