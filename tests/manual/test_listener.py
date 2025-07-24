"""
Manual test for the BPY MCP listener.

This script can be used to test the Blender extension manually
outside of Blender by connecting to the TCP server.
"""

import asyncio
import json
import socket
import struct


async def manual_test_connection(host: str = "localhost", port: int = 4777, token: str | None = None):
    """Test connection to the BPY MCP server."""
    print(f"Connecting to {host}:{port}")

    try:
        reader, writer = await asyncio.open_connection(host, port)
        print("Connected successfully!")

        # Test authentication
        auth_message = {"id": "auth_test", "token": token or "test-token-123"}

        await send_message(writer, auth_message)
        response = await receive_message(reader)
        print(f"Auth response: {response}")

        if not response.get("authenticated"):
            print("Authentication failed!")
            return

        # Test code execution
        code_message = {"id": "code_test", "code": "print('Hello from BPY MCP!')", "stream": True}

        await send_message(writer, code_message)
        response = await receive_message(reader)
        print(f"Code execution response: {response}")

        # Test Blender-specific code (this will fail outside Blender)
        blender_message = {"id": "blender_test", "code": "bpy.context.scene.name", "stream": True}

        await send_message(writer, blender_message)
        response = await receive_message(reader)
        print(f"Blender code response: {response}")

        writer.close()
        await writer.wait_closed()
        print("Connection closed")

    except ConnectionRefusedError:
        print(f"Connection refused - is the server running on {host}:{port}?")
    except Exception as e:
        print(f"Error: {e}")


async def send_message(writer: asyncio.StreamWriter, message: dict):
    """Send a JSON message over the TCP connection."""
    message_str = json.dumps(message)
    message_data = message_str.encode("utf-8")
    message_length = len(message_data)

    # Send length prefix (4 bytes, big endian)
    length_bytes = struct.pack(">I", message_length)
    writer.write(length_bytes + message_data)
    await writer.drain()


async def receive_message(reader: asyncio.StreamReader) -> dict:
    """Receive a JSON message from the TCP connection."""
    # Read length prefix
    length_data = await reader.readexactly(4)
    message_length = struct.unpack(">I", length_data)[0]

    # Read message data
    message_data = await reader.readexactly(message_length)
    message_str = message_data.decode("utf-8")

    return json.loads(message_str)


def manual_test_port_availability(host: str = "localhost", port: int = 4777) -> bool:
    """Test if the port is available or already in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            if result == 0:
                print(f"Port {port} is in use (server might be running)")
                return True
            else:
                print(f"Port {port} is available (server not running)")
                return False
    except Exception as e:
        print(f"Error checking port: {e}")
        return False


def main():
    """Main test function."""
    print("BPY MCP Manual Test")
    print("=" * 40)

    # Check if server is running
    if manual_test_port_availability():
        print("Attempting to connect...")
        asyncio.run(manual_test_connection())
    else:
        print("Server does not appear to be running.")
        print("Start Blender with the BPY MCP extension enabled first.")


if __name__ == "__main__":
    main()
