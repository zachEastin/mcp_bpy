"""Test script to check Blender MCP connection status."""

import asyncio
import json
import os
import socket
import struct
from typing import Any

import pytest


async def send_message(writer: asyncio.StreamWriter, message: dict[str, Any]) -> None:
    """Send a JSON message over the TCP connection."""
    message_str = json.dumps(message)
    message_data = message_str.encode("utf-8")
    message_length = len(message_data)

    # Send length prefix (4 bytes, big endian)
    length_bytes = struct.pack(">I", message_length)
    writer.write(length_bytes + message_data)
    await writer.drain()


async def receive_message(reader: asyncio.StreamReader) -> dict[str, Any]:
    """Receive a JSON message from the TCP connection."""
    # Read length prefix
    length_data = await reader.readexactly(4)
    message_length = struct.unpack(">I", length_data)[0]

    # Read message data
    message_data = await reader.readexactly(message_length)
    message_str = message_data.decode("utf-8")

    return json.loads(message_str)


def check_port_availability(host: str, port: int) -> bool:
    """Check if a port is open and listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)  # 5 second timeout
            result = sock.connect_ex((host, port))
            return result == 0  # 0 means connection successful
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False


@pytest.mark.asyncio
async def test_blender_connection() -> None:
    """Test the connection to Blender."""
    # Configuration
    port = int(os.getenv("BLENDER_MCP_PORT", "4777"))
    host = "localhost"
    token = os.getenv("BLENDER_MCP_TOKEN", "test-token-123")

    print("=== Blender MCP Connection Test ===")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Token: {token}")
    print()

    # Step 1: Check if port is open
    print("Step 1: Checking if port is open...")
    if check_port_availability(host, port):
        print(f"✅ Port {port} is open and accepting connections")
    else:
        print(f"❌ Port {port} is not available or not listening")
        print("Make sure Blender is running with the BPY MCP addon enabled")
        return

    # Step 2: Try to establish TCP connection
    print("\nStep 2: Attempting TCP connection...")
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=10)
        print("✅ TCP connection established successfully")
    except TimeoutError:
        print("❌ Connection timeout - Blender may not be responding")
        return
    except Exception as e:
        print(f"❌ Failed to establish TCP connection: {e}")
        return

    # Step 3: Test authentication
    print("\nStep 3: Testing authentication...")
    try:
        auth_message = {"id": "test_auth", "token": token}
        await send_message(writer, auth_message)

        # Wait for response with timeout
        response = await asyncio.wait_for(receive_message(reader), timeout=10)

        if response.get("authenticated"):
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {response}")

    except TimeoutError:
        print("❌ Authentication timeout - no response from Blender")
    except Exception as e:
        print(f"❌ Authentication error: {e}")

    # Step 4: Test code execution
    print("\nStep 4: Testing code execution...")
    try:
        test_code = """
import bpy
print("Blender version:", bpy.app.version_string)
print("Current scene:", bpy.context.scene.name)
"""

        exec_message = {"id": "test_exec", "code": test_code, "stream": False}
        await send_message(writer, exec_message)

        response = await asyncio.wait_for(receive_message(reader), timeout=15)

        if response.get("error"):
            print(f"❌ Code execution error: {response['error']}")
        else:
            print("✅ Code execution successful")
            print(f"Output: {response.get('output', 'No output')}")

    except TimeoutError:
        print("❌ Code execution timeout")
    except Exception as e:
        print(f"❌ Code execution error: {e}")

    # Cleanup
    print("\nStep 5: Cleaning up connection...")
    try:
        writer.close()
        await writer.wait_closed()
        print("✅ Connection closed successfully")
    except Exception as e:
        print(f"⚠️  Warning during cleanup: {e}")

    print("\n=== Test Complete ===")


def check_environment():
    """Check environment variables and configuration."""
    print("=== Environment Check ===")

    # Check environment variables
    port = os.getenv("BLENDER_MCP_PORT", "4777")
    token = os.getenv("BLENDER_MCP_TOKEN", "test-token-123")

    print(f"BLENDER_MCP_PORT: {port}")
    print(f"BLENDER_MCP_TOKEN: {token}")

    # Check if variables are defaults
    if port == "4777":
        print("⚠️  Using default port (4777)")
    if token == "test-token-123":
        print("⚠️  Using default token")

    print()


def print_troubleshooting_tips():
    """Print troubleshooting tips."""
    print("\n=== Troubleshooting Tips ===")
    print("1. Make sure Blender is running")
    print("2. Make sure the BPY MCP addon is installed and enabled in Blender")
    print("3. Check that the addon is listening on the correct port (4777)")
    print("4. Verify the token matches between Blender addon and MCP server")
    print("5. Try restarting Blender and then the MCP server")
    print("6. Check Blender's console for any error messages")
    print("\nStartup order that usually works:")
    print("  1. Start Blender")
    print("  2. Enable the BPY MCP addon")
    print("  3. Start the MCP server in VS Code")


def main():
    """Main test function."""
    check_environment()

    try:
        asyncio.run(test_blender_connection())
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

    print_troubleshooting_tips()


if __name__ == "__main__":
    main()
