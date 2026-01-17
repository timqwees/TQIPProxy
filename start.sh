#!/bin/bash
source venv/bin/activate
pip install "requests>=2.31.0"

echo ""
echo "> 1. Включить прокси"
echo "> 2. Выключить прокси"
echo "> 3. Запустить IP-менеджер"
echo "> 4. Выход"

read -p "Выберите дейсвтвие:" SELECT

if [ "$SELECT" = "1" ]; then
    SERVICE="Wi-Fi"
    PROXY_HOST="127.0.0.1"
    PROXY_PORT="9050"

    CURRENT_STATE=$(networksetup -getsocksfirewallproxy "$SERVICE" | grep "Enabled: Yes")

    if [ -n "$CURRENT_STATE" ]; then
        echo "SOCKS proxy is already enabled. Proceeding..."
    else
        echo "Enabling SOCKS proxy..."
        networksetup -setsocksfirewallproxy "$SERVICE" "$PROXY_HOST" "$PROXY_PORT"
        networksetup -setsocksfirewallproxystate "$SERVICE" on
        echo "SOCKS proxy enabled: $PROXY_HOST:$PROXY_PORT"
    fi

    echo "Starting Tor service..."
    brew services start tor
    sleep 5  # Wait for Tor to initialize

    python change_ip.py 0 4 #count 0 -> infinite loop, interval 4s
elif [ "$SELECT" = "2" ]; then
    echo "Отключение прокси и остановка tor..."
    SERVICE="Wi-Fi"

    # Disable SOCKS proxy
    networksetup -setsocksfirewallproxystate "$SERVICE" off
    echo "SOCKS proxy disabled"

    # Stop Tor service
    brew services stop tor
    echo "Tor service stopped"

    echo "Интернет-соединение восстановлено"
elif [ "$SELECT" = "3" ]; then
    read -p "Укажите срок работы: " TIMER
    echo "Запуск IP-менеджера... длительность $TIMER минут смена каждые 5 секунд"
    SERVICE="Wi-Fi"
    PROXY_HOST="127.0.0.1"
    PROXY_PORT="9050"

    CURRENT_STATE=$(networksetup -getsocksfirewallproxy "$SERVICE" | grep "Enabled: Yes")

    if [ -n "$CURRENT_STATE" ]; then
        echo "SOCKS proxy is already enabled. Proceeding..."
    else
        echo "Enabling SOCKS proxy..."
        networksetup -setsocksfirewallproxy "$SERVICE" "$PROXY_HOST" "$PROXY_PORT"
        networksetup -setsocksfirewallproxystate "$SERVICE" on
        echo "SOCKS proxy enabled: $PROXY_HOST:$PROXY_PORT"
    fi

    echo "Starting Tor service..."
    brew services start tor
    sleep 5  # Wait for Tor to initialize

    python change_ip.py $TIMER 10 #count 0 -> infinite loop, interval 10s
elif [ "$SELECT" = "4" ]; then
    exit
fi
