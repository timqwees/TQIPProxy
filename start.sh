#!/bin/bash
# start.sh — меню управления прокси/Tor для macOS
set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

PROXY_HOST="127.0.0.1"
PROXY_PORT="9050"
DEFAULT_INTERVAL=10
TOR_WAIT=10

if [ ! -f "venv/bin/activate" ]; then
    echo "[!] venv не найден. Создайте: python3 -m venv venv"
    exit 1
fi
# shellcheck disable=SC1091
source venv/bin/activate

if ! python -c "import requests" 2>/dev/null; then
    echo "[*] Устанавливаю requests..."
    pip install --quiet "requests[socks]>=2.31.0"
fi
if ! python -c "import stem" 2>/dev/null; then
    echo "[*] Устанавливаю stem (для NEWNYM)..."
    pip install --quiet "stem>=1.8.0"
fi

detect_service() {
    local iface svc
    iface=$(route -n get default 2>/dev/null | awk '/interface:/{print $2}')
    if [ -n "${iface:-}" ]; then
        svc=$(networksetup -listnetworkserviceorder 2>/dev/null \
              | grep -B1 "Device: ${iface}" \
              | head -1 \
              | sed -E 's/^\([0-9]+\) //')
        if [ -n "${svc:-}" ]; then
            echo "$svc"
            return
        fi
    fi
    echo "Wi-Fi"
}

enable_proxy() {
    local svc="$1"
    if networksetup -getsocksfirewallproxy "$svc" | grep -q "Enabled: Yes"; then
        echo "[*] SOCKS-прокси уже включён для \"$svc\""
    else
        echo "[*] Включаю SOCKS-прокси $PROXY_HOST:$PROXY_PORT для \"$svc\""
        networksetup -setsocksfirewallproxy "$svc" "$PROXY_HOST" "$PROXY_PORT"
        networksetup -setsocksfirewallproxystate "$svc" on
    fi
}

disable_proxy() {
    local svc="$1"
    echo "[*] Отключаю SOCKS-прокси для \"$svc\""
    networksetup -setsocksfirewallproxystate "$svc" off
}

start_tor() {
    echo "[*] Запускаю Tor..."
    brew services start tor >/dev/null 2>&1 || true
    sleep "$TOR_WAIT"
}

stop_tor() {
    echo "[*] Останавливаю Tor..."
    brew services stop tor >/dev/null 2>&1 || true
}

echo ""
echo "> 1. Включить прокси и бесконечная смена IP"
echo "> 2. Выключить прокси и остановить Tor"
echo "> 3. Запустить смену IP на время (в минутах)"
echo "> 4. Выход"
read -rp "Выберите действие: " SELECT

SERVICE_ACTIVE=$(detect_service)

case "$SELECT" in
    1)
        enable_proxy "$SERVICE_ACTIVE"
        start_tor
        python change_ip.py 0 "$DEFAULT_INTERVAL"
        ;;
    2)
        disable_proxy "$SERVICE_ACTIVE"
        stop_tor
        echo "[+] Прокси отключён, Tor остановлен"
        ;;
    3)
        read -rp "Укажите срок работы (в минутах): " TIMER
        if ! [[ "$TIMER" =~ ^[0-9]+$ ]] || [ "$TIMER" -le 0 ]; then
            echo "[!] Некорректное значение"
            exit 1
        fi
        COUNT=$(( TIMER * 60 / DEFAULT_INTERVAL ))
        [ "$COUNT" -lt 1 ] && COUNT=1
        echo "[*] Запуск на $TIMER мин (~$COUNT смен, интервал ${DEFAULT_INTERVAL}с)"
        enable_proxy "$SERVICE_ACTIVE"
        start_tor
        python change_ip.py "$COUNT" "$DEFAULT_INTERVAL"
        ;;
    4)
        exit 0
        ;;
    *)
        echo "[!] Неверный выбор"
        exit 1
        ;;
esac