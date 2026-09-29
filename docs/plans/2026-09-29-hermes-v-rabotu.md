# Hermes в работу: допуск и отбор задач (план с 29.09.2026)

Решение Алексея 29.09: Hermes не снимаем, добавляем в рабочие инструменты и нововведения не
отбрасываем. Сейчас много работы, которую можно отдать Hermes. 30.09–01.10 Алексей на
двухдневном вебинаре по Hermes.

Замер, на который опирается план: [../2026-09-29-orca-hermes-razbor.md](../2026-09-29-orca-hermes-razbor.md), раздел Hermes.

Чек-лист правится **на месте**: `⬜` → `✅` + дата + пруф. Прозой не переписывать.

## Что отдавать Hermes

Козырь Hermes — **подписка ChatGPT (Codex) вместо лимита Claude** и крон в monitor mode: модель будится, только если изменился вывод проверки.

Значит, ему уходят:
- **механика и чтение:** разборы логов, сводки, сторожа;
- **длинные прогоны**, которые сейчас жгут `claude -p`.

Ограничение из решения Алексея 04.09 в силе: клиентские автоматизации без Claude не переводить («не дай бог поломаются»). Порядок — сначала внутреннее и читающее, клиентское — только после двух недель зелёного на внутреннем.

## Допуск к работе — до первой новой задачи

Каждый пункт меняет конфиг или ключи, поэтому нужно **слово Алексея**. **Получено 29.09: «да допуск Hermes» — на D1–D4, D6, D7** (D5 — руками Алексея).

- ✅ 29.09 (слово «да допуск Hermes»): `model` → `openai-codex` / `gpt-5.6-sol`, `base_url` `chatgpt.com/backend-api/codex` — та же запись, что делает `hermes model` (`_update_config_for_provider`), `api_key`/`api_mode` локального эндпоинта сняты. `gemma4:12b` переехала в `providers.ollama-local` — только явным выбором. Проверка: `resolve_runtime_provider()` → `openai-codex`, `codex_responses`. Отдельного ключа модели для платформы в 0.21.5 не нашёл: Telegram и CLI берут `model.default`, закрепа модели у Telegram-сессии нет (`sessions.json`). Бэкап `~/.hermes/config.yaml.bak-2026-09-29-pre-dopusk`. **D1 · модель по умолчанию.** Сейчас в `config.yaml` стоит `gemma4:12b` (локальная). Последняя живая задача 17.09 на ней — ложное «Подтверждено», правка ушла не в тот файл. Поставить Codex (`openai-codex`, gpt-5.6-sol) по умолчанию для Telegram и CLI; локальную модель — только явным выбором.
- ✅ 29.09 (слово «да допуск Hermes»): `hermes cron edit b3f6f75d7045 --provider openai-codex --model gpt-5.6-sol`, в `jobs.json` проверено `openai-codex gpt-5.6-sol`, бэкап `~/.hermes/cron/jobs.json.bak-2026-09-29-pre-d2`. Живой прогон на Codex — не делался, это DoD для D4. **D2 · `kadens-razbor`.** Сейчас `claude-opus-5` через OAuth подписки Claude, а вход умер 28.09 — следующий прогон упадёт. Перевести на `openai-codex/gpt-5.6-sol`: на нём он уже шёл 02–08.09, 7 прогонов, 0 ошибок. Заодно уходит нарушение Правила 4 (механика на Opus).
- ✅ 29.09 — выключать нечего, посылка замера неверна. По исходникам 0.21.5 Desktop сам `hermes update` не запускает: `apps/desktop/src/store/updates.ts` `startUpdatePoller` раз в 24 ч и при фокусе только проверяет и показывает тост. `applyUpdates` вызывают лишь клики: кнопка Settings → Updates, тост, палитра команд, «обновить всё» (`electron/main.ts`, IPC `hermes:updates:apply`). Выключателя проверки нет. 8 обновлений с 08.09 — 8 кликов в Desktop, кем — не установлено. Codex независимо: MATCH. Правило: на тост не нажимать; раз в неделю `git log --oneline HEAD..origin/main` → прочитать → `hermes update` из терминала. Перед этим бэкап (D7). Рецепт — в `CADENCE.md`, раздел Hermes. **D3 · обновления.** Сейчас Hermes Desktop ночью сам ставит `main` (`hermes update --yes --branch main`, 8 раз с 08.09). Выключить автообновление; обновлять раз в неделю руками после `git log`.
- ✅ 29.09: `approvals.mode: manual`, `cron_mode: deny`, `unattended_mode: deny`, `deny` + 6 масок из карточки 06.09, `checkpoints.enabled: true`, `security`: `allow_private_urls`/`allow_lazy_installs`/`tirith_fail_open` = `false`. Имена ключей сверены с `hermes_cli/config_defaults.py` 0.21.5. Allowlist 128 → 11: чтение (`cat/tail/head/ls/grep/stat/date`) + `cadence-hygiene.py`. `find*` не внесён: маска открыла бы `find -delete`, а обычный `find` не гейтится. **Находка:** совпадение с allowlist одобряется ДО проверки `cron_mode` (`tools/approval.py`, `check_all_command_guards`), так что старые `python3*`, `curl*`, `git reset*` обходили запрет в кроне. Кроны: `kadens-razbor` → `terminal, file, no_mcp`; `wa-dozor-dnem` → `file, no_mcp` (было несуществующее имя `files`), пауза не снята. Шлюз перезапущен 17:03. **DoD:** ручной прогон `hermes cron run` 17:05 — Codex, 10 вызовов, 55 с, файл `briefings/kadens-razbor-today.md` записан, доставка в Telegram ok, блоков approvals 0. `cron_mode: deny` не мешает: команды крона детектор и tirith опасными не считают (проверено вызовом). Оговорка: для `~/Projects` checkpoints не срабатывают — там больше 50 000 файлов (`_MAX_FILES`). **D4 · approvals.** Задать `approvals.mode: manual`, `cron_mode: deny`, `unattended_mode: deny`, `checkpoints.enabled: true`; кронам — явные `enabled_toolsets`; allowlist (128 масок) срезать до чтения. Готовый YAML — в карточке `~/Projects/tasks/inbox/2026-09-06-hermes-ustanovka-vs-gayd.md`, раздел «Дёшево».
- ⬜ **D5 · Full Disk Access** — по карточке 06.09 выдан. Снять в Системных настройках — только руками Алексея.
- ✅ 29.09: раздел «Hermes (29.09.2026)» в `~/Projects/CADENCE.md` (локальный, не в git): `ai.hermes.gateway`, `kadens-razbor`, `wa-dozor-dnem` (пауза), `com.alexey.hermes.backup`. Колонки: триггер, код, ключи и что физически может, лог, владелец, health. Плюс паспорт бэкапа и рецепт ручного обновления. **D6 · реестр.** Строки в `~/Projects/CADENCE.md`: шлюз `ai.hermes.gateway` (KeepAlive) и каждый крон — владелец, ключи, лог, health. Сейчас их там нет.
- ✅ 29.09: `~/.claude/scripts/hermes-backup.sh` + launchd `com.alexey.hermes.backup` (вс). `state.db` и `cron/*.db` снимаются `sqlite3 .backup` + `integrity_check`, без `-wal/-shm`; `config.yaml`, `cron/`, `memories/`, `SOUL.md` — копией; `.env` и `auth.json` не берутся. Архив — в `~/Backups/hermes/` (права 700/600, хранятся 8, без шифрования). Живой прогон через launchd в 17:07: 5,5 МБ, exit 0, в снимке столько же сообщений, сколько в живой базе, `cadence-hygiene` — «в срок». Квота CADENCE «1 новый = 2 снятых» не соблюдена: джоб поставлен по прямому слову (D7). Гейт: Codex `exec -s read-only` перепроверил конфиг, кроны, живой прогон, D3 и бэкап — 9/9 MATCH. **D7 · бэкап** `~/.hermes` (config, cron, memories, state.db): раз в неделю `tar`. Сейчас бэкапа нет.

## Вопросы на вебинар 30.09–01.10

Ответы записать сюда же, одной строкой каждый, с источником (слайд или минута записи).

- ⬜ стабильный канал обновлений вместо `main` — есть ли, как включить;
- ⬜ безопасный режим для крона, который читает чужой текст (WhatsApp, почта): `terminal.backend: docker`, `HERMES_WRITE_SAFE_ROOT`, что рекомендуют авторы;
- ⬜ закрепить модель за платформой (Telegram / cron / CLI) и провайдер для fallback;
- ⬜ делегирование и kanban: может ли Hermes раздавать задачи другим агентам (Codex, Claude) и собирать итог — как это соотносится с Orca, чтобы не завести два оркестратора;
- ⬜ вход Anthropic: какой способ авторы считают штатным (API-ключ или OAuth подписки) и как не делить OAuth с Claude Code — совет 01.09 подозревал общий токен в отзывах 401;
- ⬜ что из показанного на вебинаре закрывает задачи из списка ниже лучше, чем launchd + `claude -p`.

## Кандидаты на отдачу — отбор после вебинара

Каждый кандидат проходит один вопрос: механика или чтение, внутреннее, есть проверяемый выход? Проходит — Hermes, Codex, monitor mode. Не проходит — остаётся где был.

- ⬜ `kadens-razbor` — уже у Hermes, после D2 держать;
- ⬜ `wa-dozor-dnem` — на паузе с 10.09 по слову Алексея; вернуть только его словом;
- ⬜ список внутренних читающих джобов на `claude -p` из `~/Projects/CADENCE.md` (сторожа, разборы, сводки) — выписать с расходом, выбрать 1–2 на пробу;
- ⬜ телефонные задачи через Telegram — только после D1, с проверкой результата, не на слово агента.

## Решает Алексей

- «да допуск Hermes» — D1–D4, D6, D7 (D5 — руками);
- какие 1–2 задачи отдать первыми после вебинара;
- делить ли оркестрацию между Hermes и Orca, или Hermes — только исполнитель на Codex.
