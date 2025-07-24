"""Simple port scanner to check what ports are open on localhost."""

import socket


def scan_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a specific port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception:
        return False


def scan_port_range(host: str, start_port: int, end_port: int) -> list[int]:
    """Scan a range of ports and return the open ones."""
    open_ports = []

    print(f"Scanning ports {start_port}-{end_port} on {host}...")

    for port in range(start_port, end_port + 1):
        if scan_port(host, port, timeout=0.5):
            open_ports.append(port)
            print(f"✅ Port {port} is open")

    return open_ports


def main():
    """Main function to scan for open ports."""
    host = "localhost"

    print("=== Port Scanner for Blender MCP ===")
    print(f"Scanning {host} for common and Blender-related ports...\n")

    # Check the expected Blender MCP port
    target_port = 4777
    print(f"Checking target port {target_port}:")
    if scan_port(host, target_port):
        print(f"✅ Port {target_port} is OPEN - Blender should be reachable")
    else:
        print(f"❌ Port {target_port} is CLOSED - Blender MCP addon not running")

    print()

    # Scan common ports that Blender or similar apps might use
    common_ports = [4776, 4777, 4778, 8080, 8888, 9999, 7777, 5555]
    print("Checking common ports that might be used by Blender addons:")
    open_common = []

    for port in common_ports:
        if scan_port(host, port):
            open_common.append(port)
            print(f"✅ Port {port} is open")

    if not open_common:
        print("❌ No common ports are open")

    print()

    # Ask user if they want to scan a broader range
    print("Scanning broader range (4770-4790) for any Blender-related services:")
    open_range = scan_port_range(host, 4770, 4790)

    if not open_range:
        print("❌ No ports found in range 4770-4790")

    print("\n=== Summary ===")
    print(f"Target port {target_port}: {'OPEN' if scan_port(host, target_port) else 'CLOSED'}")

    all_open = set(open_common + open_range)
    if all_open:
        print(f"Other open ports found: {sorted(all_open)}")
    else:
        print("No other relevant ports found open")

    print("\n=== Next Steps ===")
    if not scan_port(host, target_port):
        print("1. Make sure Blender is running")
        print("2. Check that the BPY MCP addon is installed in Blender")
        print("3. Enable the BPY MCP addon in Blender's preferences")
        print("4. Check Blender's console for any addon error messages")
        print("5. Verify the addon configuration (port and token)")
    else:
        print("Port 4777 is open! The connection issue might be with authentication or protocol.")


if __name__ == "__main__":
    main()
