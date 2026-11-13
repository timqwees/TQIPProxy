#!/usr/bin/env python3
"""change_ip.py — автоматическая смена IP через Tor.

Использование:
    python change_ip.py <count> [interval]
    count=0 — бесконечный цикл
    interval — пауза между сменами (сек), по умолчанию 10

Смена IP:
    1) Сначала пробуем NEWNYM через ControlPort (быстро, без перезапуска).
    2) Если ControlPort недоступен — перезапускаем Tor через brew services.
"""

import argparse
import socket
import subprocess
import sys
import time
from datetime import datetime

import requests

PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050',
}

TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051

try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False


def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open('change_ip.log', 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def check_tor_ip(timeout: int = 30):
    """Возвращает (ip, is_tor) или (None, False) при ошибке."""
    try:
        r = requests.get(
            'https://check.torproject.org/api/ip',
            proxies=PROXY,
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        return data.get('IP'), bool(data.get('IsTor', False))
    except Exception as e:
        log(f"Ошибка проверки IP: {e}")
        return None, False


def port_open(host: str = '127.0.0.1', port: int = TOR_SOCKS_PORT,
              timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_for_tor(timeout: int = 60) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if port_open(port=TOR_SOCKS_PORT):
            return True
        time.sleep(1)
    return False


def try_newnym() -> bool:
    """Пробует сменить цепочку через ControlPort. True — если получилось."""
    if not STEM_AVAILABLE:
        return False
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as ctrl:
            ctrl.authenticate()
            ctrl.signal(Signal.NEWNYM)
        log("Отправлен сигнал NEWNYM")
        return True
    except Exception as e:
        log(f"NEWNYM недоступен ({e}). Убедитесь, что в torrc есть ControlPort 9051.")
        return False


def restart_tor_service() -> bool:
    try:
        subprocess.run(
            ['brew', 'services', 'restart', 'tor'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log("Tor перезапущен")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Не удалось перезапустить Tor: {e}")
        return False


def renew_ip() -> bool:
    if try_newnym():
        time.sleep(2)
        return True
    log("Перезапуск Tor...")
    if not restart_tor_service():
        return False
    if not wait_for_tor(timeout=60):
        log("Tor не поднялся за отведённое время")
        return False
    time.sleep(3)
    return True


def change_ip_once() -> bool:
    current_ip, is_tor = check_tor_ip()
    if current_ip:
        log(f"Текущий IP: {current_ip} (Tor: {is_tor})")
    else:
        log("Не удалось получить текущий IP")

    if not renew_ip():
        return False

    new_ip, is_tor = check_tor_ip()
    if not new_ip:
        log("Не удалось получить новый IP")
        return False

    log(f"Новый IP: {new_ip} (Tor: {is_tor})")
    if current_ip is None:
        log("Сравнить не с чем (старый IP неизвестен)")
    elif new_ip != current_ip:
        log("✓ IP изменён успешно")
    else:
        log("⚠ IP не изменился")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Смена IP через Tor',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('count', type=int,
                        help='Количество смен (0 — бесконечно)')
    parser.add_argument('interval', type=int, nargs='?', default=10,
                        help='Интервал между сменами, сек')
    parser.add_argument('--min-interval', type=int, default=2,
                        help='Минимальный допустимый интервал, сек')
    args = parser.parse_args()

    interval = max(args.min_interval, args.interval)

    if not wait_for_tor(timeout=60):
        log("Tor не слушает порт 9050. Проверьте: brew services list")
        sys.exit(1)

    try:
        if args.count == 0:
            log(f"Бесконечная смена IP, интервал {interval}с")
            i = 0
            while True:
                i += 1
                log(f"--- Итерация {i} ---")
                change_ip_once()
                log(f"Пауза {interval}с")
                time.sleep(interval)
        else:
            log(f"Смена IP {args.count} раз, интервал {interval}с")
            for i in range(1, args.count + 1):
                log(f"--- Итерация {i} ---")
                change_ip_once()
                if i < args.count and interval > 0:
                    log(f"Пауза {interval}с")
                    time.sleep(interval)
    except KeyboardInterrupt:
        log("Остановлено пользователем")


if __name__ == '__main__':
    main()