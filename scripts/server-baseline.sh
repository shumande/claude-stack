#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# server-baseline.sh — базовая защита Linux-сервера. Идемпотентен: можно гонять
# повторно. Написан 22.08.2026 после разбора двух живых VPS, где нашлось:
#   57.677 попыток подбора пароля · вход root по паролю открыт · файрвола нет ·
#   fail2ban нет · контейнер не обновлялся 5 месяцев · порт headless-браузера
#   торчал в интернет · сертификат просрочен 57 дней и никто не знал.
#
# Применение:  scp server-baseline.sh root@HOST:/root/ && ssh root@HOST 'bash /root/server-baseline.sh'
# ВАЖНО: до запуска убедись, что твой ключ уже в ~/.ssh/authorized_keys —
#        скрипт отключает вход по паролю и без ключа ты потеряешь доступ
#        (аварийный вход остаётся через консоль в панели хостера).
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "нужен root"; exit 1; }

say() { printf "\n\033[1m▸ %s\033[0m\n" "$1"; }

say "0. Предохранитель: есть ли ключ для входа"
KEYS=$(grep -c "^ssh-" /root/.ssh/authorized_keys 2>/dev/null || echo 0)
[ "$KEYS" -gt 0 ] || { echo "❌ В /root/.ssh/authorized_keys нет ни одного ключа. Останавливаюсь:"
                       echo "   отключить пароль сейчас = потерять доступ к машине."; exit 1; }
echo "ключей найдено: $KEYS"

say "1. SSH: только по ключу"
# Имя 00- обязательно: sshd берёт ПЕРВОЕ вхождение параметра, а cloud-init
# кладёт свой 50-cloud-init.conf с PasswordAuthentication yes и перебивает всё,
# что лежит с бо́льшим номером. Проверено на живой машине 22.08.2026.
cat > /etc/ssh/sshd_config.d/00-hardening.conf <<'CONF'
PasswordAuthentication no
PermitRootLogin prohibit-password
KbdInteractiveAuthentication no
MaxAuthTries 3
X11Forwarding no
CONF
sshd -t && systemctl reload ssh
echo "итог: $(sshd -T | grep -E '^(passwordauthentication|permitrootlogin)' | tr '\n' ' ')"

say "2. fail2ban"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fail2ban >/dev/null
cat > /etc/fail2ban/jail.local <<'CONF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 3
backend  = systemd

[sshd]
enabled = true
mode    = aggressive
CONF
systemctl enable --now fail2ban >/dev/null 2>&1
systemctl restart fail2ban
echo "fail2ban: $(systemctl is-active fail2ban)"

say "3. Файрвол"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ufw >/dev/null
ufw allow 22/tcp  comment 'SSH (только по ключу)' >/dev/null
ufw allow 80/tcp  comment 'HTTP -> редирект' >/dev/null
ufw allow 443/tcp comment 'HTTPS' >/dev/null
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw --force enable >/dev/null
echo "ufw: $(ufw status | head -1)"

say "4. Автообновления безопасности"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq unattended-upgrades >/dev/null
systemctl enable --now unattended-upgrades >/dev/null 2>&1
echo "unattended-upgrades: $(systemctl is-active unattended-upgrades)"

say "5. ПРОВЕРКА: что реально торчит в интернет"
# ufw НЕ закрывает порты, опубликованные Docker: он пишет правила в nat-таблицу
# мимо ufw. Единственный рабочий способ — публиковать порт как 127.0.0.1:PORT:PORT
# в compose. Поймано 22.08.2026: headless-браузер висел на 0.0.0.0:3000.
EXPOSED=$(ss -tlnH | awk '$4 !~ /^(127\.|\[::1\])/ {split($4,a,":"); print a[length(a)]}' | sort -un | tr '\n' ' ')
echo "открыто наружу: $EXPOSED"
for p in $EXPOSED; do
  case "$p" in
    22|80|443) ;;
    *) echo "  ⚠️  порт $p не входит в базовый набор — проверь, нужен ли он снаружи."
       echo "      если это Docker: в compose поменяй \"$p:$p\" на \"127.0.0.1:$p:$p\"" ;;
  esac
done

say "ГОТОВО. Дальше — поставь ежемесячную проверку:"
echo "  scp server-maintenance-check.sh root@HOST:/root/monthly-maintenance.sh"
echo "  и создай /root/.maintenance.env (см. docs/server-baseline.md)"
