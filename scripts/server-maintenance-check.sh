#!/usr/bin/env bash
# Ежемесячная проверка обслуживания сервера. Поставлено 22.08.2026.
# ТОЛЬКО ЧИТАЕТ И ДОКЛАДЫВАЕТ — ничего не обновляет и не перезагружает сам.
# Настройки хоста: /root/.maintenance.env (TELEGRAM_BOT_TOKEN, CHAT_ID,
#   HOST_LABEL, N8N_CONTAINER, N8N_URL, COMPOSE_FILE — последние четыре необязательны)
set -uo pipefail
source /root/.maintenance.env
LABEL="${HOST_LABEL:-$(hostname)}"
IP=$(curl -s -4 -m 5 ifconfig.me 2>/dev/null || echo "?")
L=()
L+=("🔧 <b>Обслуживание: $LABEL ($IP)</b>")
L+=("$(date '+%d.%m.%Y'), аптайм $(uptime -p | sed 's/up //')")
L+=("")

SEC=$(/usr/lib/update-notifier/apt-check 2>&1 | cut -d';' -f2); ALL=$(/usr/lib/update-notifier/apt-check 2>&1 | cut -d';' -f1)
if [ "${SEC:-0}" -gt 0 ]; then L+=("⚠️ Пакеты: <b>$SEC security</b> из $ALL ждут — <code>apt update && apt upgrade</code>")
else L+=("✅ Пакеты: security-обновлений нет (всего ${ALL:-0})"); fi
if [ -f /var/run/reboot-required ]; then
  L+=("⚠️ <b>Нужна перезагрузка</b> — $(head -3 /var/run/reboot-required.pkgs 2>/dev/null | tr '\n' ' ')")
else L+=("✅ Ядро актуально: $(uname -r)"); fi

if [ -n "${N8N_CONTAINER:-}" ] && docker inspect "$N8N_CONTAINER" >/dev/null 2>&1; then
  CUR=$(grep -oP 'n8nio/n8n:\K[0-9.]+' "${COMPOSE_FILE:-/root/docker-compose.yaml}" 2>/dev/null || echo "не закреплена")
  LATEST=$(curl -s -m 10 https://api.github.com/repos/n8n-io/n8n/releases/latest 2>/dev/null | grep -oP '"tag_name":\s*"n8n@\K[0-9.]+' | head -1)
  RUN=$(docker exec "$N8N_CONTAINER" n8n --version 2>/dev/null | tail -1)
  if [ -n "$LATEST" ] && [ "$RUN" != "$LATEST" ]; then
    L+=("⚠️ n8n: работает <b>$RUN</b>, вышла <b>$LATEST</b>")
    L+=("   правь версию в ${COMPOSE_FILE:-/root/docker-compose.yaml} → <code>docker compose up -d</code>, СНАЧАЛА бэкап")
  else L+=("✅ n8n $RUN — свежая"); fi
  H=$(curl -s -m 10 http://127.0.0.1:5678/healthz 2>/dev/null)
  [[ "$H" == *'"ok"'* ]] && L+=("✅ n8n жив (локальная проверка)") || L+=("🔴 <b>n8n НЕ отвечает локально</b>")
  if [ -n "${N8N_URL:-}" ]; then
    PUB=$(curl -s -o /dev/null -w '%{http_code}' -m 10 "$N8N_URL/" 2>/dev/null)
    [ "$PUB" = "200" ] && L+=("✅ снаружи отвечает 200") || L+=("ℹ️ снаружи HTTP $PUB (может быть Cloudflare, не тревога)")
  fi
fi

OLD=$(docker ps --format '{{.Names}}|{{.Image}}|{{.RunningFor}}' 2>/dev/null | grep -E 'months|year' | wc -l)
[ "${OLD:-0}" -gt 0 ] && L+=("⚠️ Контейнеров без пересоздания >1 мес: <b>$OLD</b> — <code>docker ps</code>")



# Сертификат проверяем ПО ФАКТУ ОТДАЧИ на 443, а не по файлам на диске:
# traefik держит их в acme.json, и просроченный сертификат может месяцами
# прятаться за Cloudflare (поймано 22.08.2026 — просрочка 57 дней).
for h in ${CERT_HOSTS:-}; do
  END=$(echo | timeout 12 openssl s_client -connect 127.0.0.1:443 -servername "$h" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  if [ -z "$END" ]; then L+=("⚠️ Сертификат $h: не смог прочитать"); continue; fi
  D=$(( ($(date -d "$END" +%s) - $(date +%s)) / 86400 ))
  if [ "$D" -lt 0 ]; then L+=("🔴 <b>Сертификат $h ПРОСРОЧЕН на $((0-D)) дн.</b>")
  elif [ "$D" -lt 21 ]; then L+=("⚠️ Сертификат $h: осталось <b>$D дн.</b>")
  else L+=("✅ Сертификат $h (отдаётся): $D дн."); fi
done
BANS=$(fail2ban-client status sshd 2>/dev/null | grep -oP 'Total banned:\s*\K[0-9]+')
[ -n "$BANS" ] && L+=("🛡 fail2ban забанил: <b>$BANS</b>") || L+=("🔴 <b>fail2ban не установлен</b>")
PW=$(sshd -T 2>/dev/null | grep -oP '^passwordauthentication \K\w+')
[ "$PW" = "no" ] && L+=("✅ SSH: только по ключу") || L+=("🔴 <b>SSH: вход по паролю ОТКРЫТ</b>")
ufw status 2>/dev/null | grep -q "Status: active" && L+=("✅ Файрвол активен") || L+=("🔴 <b>Файрвол выключен</b>")
L+=("🔌 Открыто наружу: <code>$(ss -tlnH | awk '$4 !~ /^(127\.|\[::1\])/ {split($4,a,":"); print a[length(a)]}' | sort -un | tr '\n' ' ')</code>")
L+=("💾 Диск: $(df -h / | awk 'NR==2{print $5" занято, "$4" свободно"}') · RAM: $(free -m | awk 'NR==2{print int($3/$2*100)"%"}')")
[ -d /root/backups ] && L+=("📦 Бэкапы: $(du -sh /root/backups 2>/dev/null | cut -f1)")

MSG=$(printf '%s\n' "${L[@]}")
curl -s -m 20 -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" -d "parse_mode=HTML" --data-urlencode "text=${MSG}" -o /tmp/tg-result.json -w "telegram HTTP %{http_code}\n"
grep -q '"ok":true' /tmp/tg-result.json && echo "доставлено" || { echo "НЕ ДОСТАВЛЕНО:"; head -c 300 /tmp/tg-result.json; }
printf '%s\n' "${L[@]}" | sed 's/<[^>]*>//g'
