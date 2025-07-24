"""Quick test to execute simple Python in Blender."""

import asyncio
import json
import struct


async def send_message(writer, message):
    """Send a JSON message."""
    message_str = json.dumps(message)
    message_data = message_str.encode("utf-8")
    message_length = len(message_data)
    length_bytes = struct.pack(">I", message_length)
    writer.write(length_bytes + message_data)
    await writer.drain()


async def receive_message(reader):
    """Receive a JSON message."""
    length_data = await reader.readexactly(4)
    message_length = struct.unpack(">I", length_data)[0]
    message_data = await reader.readexactly(message_length)
    message_str = message_data.decode("utf-8")
    return json.loads(message_str)


async def quick_test():
    """Quick test of code execution."""
    try:
        reader, writer = await asyncio.open_connection("localhost", 4777)
        
        # Authenticate
        auth_msg = {"id": "auth", "token": "test-token-123"}
        await send_message(writer, auth_msg)
        auth_response = await receive_message(reader)
        print("Auth response:", auth_response)
        
        if auth_response.get("authenticated"):
            # Test simple code
            code_msg = {"id": "test", "code": "print('Hello from Blender!')\nprint('2 + 2 =', 2 + 2)"}
            await send_message(writer, code_msg)
            code_response = await receive_message(reader)
            print("Code response:", code_response)
            
            # Test with bpy import
            bpy_msg = {"id": "bpy_test", "code": "import bpy\nprint('Blender version:', bpy.app.version_string)"}
            await send_message(writer, bpy_msg)
            bpy_response = await receive_message(reader)
            print("BPY response:", bpy_response)
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(quick_test())
