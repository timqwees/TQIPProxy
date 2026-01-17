#!/usr/bin/env python3
import requests
import time
import subprocess
import sys

def check_tor_ip():
    """Check current Tor IP"""
    try:
        response = requests.get(
            'https://check.torproject.org/api/ip',
            proxies={'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'},
            timeout=30  # Increase timeout to 30 seconds
        )
        return response.json()['IP']
    except Exception as e:
        print(f"Error checking IP: {e}")
        return None

def restart_tor():
    """Restart Tor service on macOS"""
    try:
        subprocess.run(['brew', 'services', 'restart', 'tor'], check=True)
        print("Tor service restarted")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart Tor: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python change_ip.py <count> [interval]")
        print("Example: python change_ip.py 5 10")
        sys.exit(1)

    count = int(sys.argv[1]) #args[1] -> count
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5 #args[2] -> interval

    print(f"Changing IP {count} times with {interval}s intervals")

    if count == 0:  # Infinite loop
        i = 0
        while True:
            iteration = i + 1
            print(f"\n--- Iteration {iteration} ---")

            # Get current IP
            current_ip = check_tor_ip()
            if current_ip:
                print(f"Current IP: {current_ip}")

            # Restart Tor to get new IP
            print("Restarting Tor...")
            if restart_tor():
                # Wait for Tor to establish connection
                print("Waiting for Tor to establish connection...")
                time.sleep(15)  # Increased wait time to 15 seconds

                # Check new IP
                new_ip = check_tor_ip()
                if new_ip:
                    print(f"New IP: {new_ip}")
                    if current_ip and new_ip != current_ip:
                        print("✓ IP changed successfully!")
                    else:
                        print("⚠ IP did not change")

            if interval > 0:
                print(f"Waiting {interval} seconds...")
                time.sleep(interval)

            i += 1
    else:
        for i in range(count):
            iteration = i + 1
            print(f"\n--- Iteration {iteration} ---")

            # Get current IP
            current_ip = check_tor_ip()
            if current_ip:
                print(f"Current IP: {current_ip}")

            # Restart Tor to get new IP
            print("Restarting Tor...")
            if restart_tor():
                # Wait for Tor to establish connection
                print("Waiting for Tor to establish connection...")
                time.sleep(15)  # Increased wait time to 15 seconds

                # Check new IP
                new_ip = check_tor_ip()
                if new_ip:
                    print(f"New IP: {new_ip}")
                    if current_ip and new_ip != current_ip:
                        print("✓ IP changed successfully!")
                    else:
                        print("⚠ IP did not change")

            if interval > 0:
                print(f"Waiting {interval} seconds...")
                time.sleep(interval)

if __name__ == "__main__":
    main()
