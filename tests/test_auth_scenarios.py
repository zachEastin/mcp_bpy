"""Test authentication scenarios with Blender MCP."""

import asyncio
import json
import struct


async def send_message(writer: asyncio.StreamWriter, message: dict) -> None:
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


async def test_auth_scenarios():
    """Test different authentication scenarios."""
    host = "localhost"
    port = 4777
    
    print("=== Blender MCP Authentication Tests ===\n")
    
    # Test 1: No token provided
    print("Test 1: Connecting without any token...")
    try:
        reader, writer = await asyncio.open_connection(host, port)
        
        # Try to execute code without authentication
        message = {"id": "test_no_auth", "code": "print('Hello from Blender')"}
        await send_message(writer, message)
        response = await receive_message(reader)
        
        print(f"Response: {response}")
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test 2: With default token
    print("Test 2: Connecting with default token 'test-token-123'...")
    try:
        reader, writer = await asyncio.open_connection(host, port)
        
        # Try authentication with default token
        auth_message = {"id": "test_auth", "token": "test-token-123"}
        await send_message(writer, auth_message)
        response = await receive_message(reader)
        
        print(f"Auth response: {response}")
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Test 3: Check if no token is required
    print("Test 3: Testing if authentication is disabled...")
    try:
        reader, writer = await asyncio.open_connection(host, port)
        
        # Try to authenticate with an empty/dummy token to see response
        auth_message = {"id": "test_auth", "token": ""}
        await send_message(writer, auth_message)
        response = await receive_message(reader)
        
        print(f"Empty token response: {response}")
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    print("=== Instructions ===")
    print("If you see 'Authentication failed: invalid token', you need to:")
    print("1. Check Blender's console (Window > Toggle System Console)")
    print("2. Look for a line like 'BPY MCP: Authentication token: <some-random-token>'")
    print("3. Set the BLENDER_MCP_TOKEN environment variable to that token")
    print("4. OR disable authentication in Blender addon preferences")
    print("\nTo disable authentication:")
    print("1. Go to Edit > Preferences > Add-ons")
    print("2. Find 'BPY MCP' addon")
    print("3. Uncheck 'Require Authentication Token'")
    print("4. Restart the server")


if __name__ == "__main__":
    asyncio.run(test_auth_scenarios())
