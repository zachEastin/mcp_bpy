"""FastMCP server for Blender Add-on management."""

import asyncio
import json
import os
import struct
from contextlib import asynccontextmanager
from typing import Any

from mcp import McpError
from mcp.server.fastmcp import FastMCP
from mcp.types import ErrorData

# Global connection state
_reader: asyncio.StreamReader | None = None
_writer: asyncio.StreamWriter | None = None
_connection_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app):
    """Manage the lifecycle of the Blender connection."""
    global _reader, _writer

    # Get port from environment or use default
    port = int(os.getenv("BLENDER_MCP_PORT", "4777"))
    host = "localhost"

    print(f"Attempting to connect to Blender on {host}:{port}")

    try:
        # Try to connect to Blender
        _reader, _writer = await asyncio.open_connection(host, port)
        print(f"Connected to Blender on {host}:{port}")

        # Authenticate if needed
        auth_message = {"id": "startup_auth", "token": os.getenv("BLENDER_MCP_TOKEN", "test-token-123")}
        await send_message(_writer, auth_message)
        response = await receive_message(_reader)

        if response.get("authenticated"):
            print("Successfully authenticated with Blender")
        else:
            print("Warning: Authentication may have failed")

    except Exception as e:
        print(f"Warning: Could not connect to Blender: {e}")
        print("Server will start but run_python tool will fail until Blender is connected")
        _reader = None
        _writer = None

    try:
        yield
    finally:
        # Cleanup connection
        if _writer:
            _writer.close()
            await _writer.wait_closed()
        _reader = None
        _writer = None
        print("Disconnected from Blender")


# Initialize the MCP server with lifespan
mcp = FastMCP("BPYMCP", version="0.1.0", lifespan=lifespan)


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


@mcp.tool()
def hello_blender() -> str:
    """A simple test tool that returns a greeting from the Blender MCP server."""
    return "Hello from BPYMCP! Ready to manage Blender add-ons."


@mcp.tool()
async def run_python(code: str, stream: bool = False) -> dict[str, str | None]:
    """Execute Python code in the attached Blender instance.

    Args:
        code: Python code to execute in Blender
        stream: Whether to stream the output (currently ignored, always returns full result)

    Returns:
        dict with 'output' and 'error' keys containing execution results

    Raises:
        McpError: If not connected to Blender or execution fails
    """
    global _reader, _writer

    async with _connection_lock:
        if not _reader or not _writer:
            raise McpError(
                ErrorData(
                    code=4001,
                    message="Not connected to Blender. Ensure Blender is running with BPY MCP extension enabled.",
                )
            )

        try:
            # Generate unique message ID
            import uuid

            message_id = str(uuid.uuid4())

            # Send code execution request
            message = {"id": message_id, "code": code, "stream": stream}

            await send_message(_writer, message)

            if stream:
                # Handle streaming responses
                output_chunks = []

                while True:
                    response = await receive_message(_reader)

                    if response.get("id") != message_id:
                        continue  # Ignore messages for other requests

                    # Check for errors
                    if response.get("error"):
                        raise McpError(ErrorData(code=4002, message=f"Blender execution error: {response['error']}"))

                    # Handle streaming chunk
                    if "chunk" in response:
                        chunk = response["chunk"]
                        output_chunks.append(chunk)
                        print(f"[STREAM] {chunk}")  # Output to console for real-time viewing

                    # Check if streaming is complete
                    if response.get("stream_end", False):
                        break

                # Return consolidated output
                full_output = "\n".join(output_chunks) if output_chunks else (response.get("output") or "")
                return {"output": full_output, "error": response.get("error")}

            else:
                # Handle regular non-streaming response
                response = await receive_message(_reader)

                # Check for errors in response
                if response.get("error"):
                    raise McpError(ErrorData(code=4002, message=f"Blender execution error: {response['error']}"))

                # Return structured result
                return {"output": response.get("output") or "", "error": response.get("error")}

        except TimeoutError as e:
            raise McpError(ErrorData(code=4003, message="Timeout waiting for Blender response")) from e
        except ConnectionError as e:
            raise McpError(ErrorData(code=4004, message=f"Connection to Blender lost: {e}")) from e
        except Exception as e:
            raise McpError(ErrorData(code=4000, message=f"Unexpected error communicating with Blender: {e}")) from e


@mcp.tool()
async def diagnose_connection() -> dict[str, str | bool]:
    """Diagnose the connection status between MCP server and Blender.

    This tool performs comprehensive connection tests and provides specific
    instructions if issues are found. Use this tool whenever you suspect
    connection problems or before performing complex Blender operations.

    Returns:
        dict: Detailed connection status and instructions

    Raises:
        McpError: Never raises - always returns diagnostic information
    """
    global _reader, _writer

    diagnosis = {
        "status": "unknown",
        "port_open": False,
        "tcp_connected": False,
        "authenticated": False,
        "code_execution": False,
        "blender_version": "",
        "instructions": "",
        "success": False,
    }

    try:
        # Step 1: Check if port is available
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            result = sock.connect_ex(("localhost", 4777))
            diagnosis["port_open"] = result == 0

        if not diagnosis["port_open"]:
            diagnosis["status"] = "port_closed"
            diagnosis["instructions"] = (
                "❌ BLENDER NOT LISTENING: Port 4777 is not open.\n\n"
                "REQUIRED ACTIONS:\n"
                "1. Ensure Blender is running\n"
                "2. In Blender: Edit > Preferences > Add-ons\n"
                "3. Find 'BPY MCP' addon and enable it\n"
                "4. If already enabled, disable and re-enable it\n"
                "5. Check Blender console for 'BPY MCP: Server started' message\n"
                "6. Then restart this MCP server (restart VS Code)\n\n"
                "⚠️ DO NOT attempt any Blender operations until connection is restored!"
            )
            return diagnosis

        # Step 2: Test TCP connection
        async with _connection_lock:
            if not _reader or not _writer:
                diagnosis["tcp_connected"] = False
                diagnosis["status"] = "no_connection"
                diagnosis["instructions"] = (
                    "❌ NO MCP CONNECTION: TCP connection not established.\n\n"
                    "REQUIRED ACTIONS:\n"
                    "1. Restart VS Code to reset the MCP server\n"
                    "2. Ensure Blender MCP addon is running (check previous step)\n"
                    "3. Wait for MCP server to reconnect automatically\n\n"
                    "⚠️ DO NOT attempt any Blender operations until connection is restored!"
                )
                return diagnosis

            diagnosis["tcp_connected"] = True

            # Step 3: Test authentication
            try:
                import uuid

                auth_id = str(uuid.uuid4())
                auth_message = {"id": auth_id, "token": os.getenv("BLENDER_MCP_TOKEN", "test-token-123")}

                await send_message(_writer, auth_message)
                auth_response = await receive_message(_reader)

                if auth_response.get("authenticated"):
                    diagnosis["authenticated"] = True
                    diagnosis["blender_version"] = auth_response.get("blender_version", "Unknown")
                else:
                    diagnosis["status"] = "auth_failed"
                    diagnosis["instructions"] = (
                        "❌ AUTHENTICATION FAILED: Invalid token or auth disabled.\n\n"
                        "REQUIRED ACTIONS:\n"
                        "1. Check Blender console for authentication token\n"
                        "2. Set environment variable: BLENDER_MCP_TOKEN=<token>\n"
                        "3. OR disable authentication in Blender addon preferences\n"
                        "4. Restart VS Code MCP server\n\n"
                        "⚠️ DO NOT attempt any Blender operations until authentication works!"
                    )
                    return diagnosis

                # Step 4: Test code execution
                test_id = str(uuid.uuid4())
                test_message = {"id": test_id, "code": "import bpy; print(f'Test OK: {bpy.app.version_string}')"}

                await send_message(_writer, test_message)
                test_response = await receive_message(_reader)

                if test_response.get("error"):
                    diagnosis["status"] = "execution_failed"
                    diagnosis["instructions"] = (
                        f"❌ CODE EXECUTION FAILED: {test_response['error']}\n\n"
                        "REQUIRED ACTIONS:\n"
                        "1. Restart Blender MCP addon:\n"
                        "   - Edit > Preferences > Add-ons\n"
                        "   - Disable 'BPY MCP' addon\n"
                        "   - Re-enable 'BPY MCP' addon\n"
                        "2. Restart VS Code to reset MCP server\n"
                        "3. Run this diagnostic again\n\n"
                        "⚠️ DO NOT attempt any Blender operations until this is fixed!"
                    )
                    return diagnosis

                diagnosis["code_execution"] = True
                diagnosis["status"] = "fully_connected"
                diagnosis["success"] = True
                diagnosis["instructions"] = (
                    f"✅ CONNECTION PERFECT!\n\n"
                    f"Blender Version: {diagnosis['blender_version']}\n"
                    f"Authentication: Working\n"
                    f"Code Execution: Working\n\n"
                    f"🚀 Ready for Blender operations!"
                )

            except Exception as e:
                diagnosis["status"] = "communication_error"
                diagnosis["instructions"] = (
                    f"❌ COMMUNICATION ERROR: {str(e)}\n\n"
                    "REQUIRED ACTIONS:\n"
                    "1. Restart Blender MCP addon (disable/enable in preferences)\n"
                    "2. Restart VS Code to reset MCP server\n"
                    "3. Ensure no firewall is blocking port 4777\n"
                    "4. Run this diagnostic again\n\n"
                    "⚠️ DO NOT attempt any Blender operations until connection is restored!"
                )

    except Exception as e:
        diagnosis["status"] = "diagnostic_error"
        diagnosis["instructions"] = (
            f"❌ DIAGNOSTIC ERROR: {str(e)}\n\n"
            "EMERGENCY ACTIONS:\n"
            "1. Restart Blender completely\n"
            "2. Restart VS Code completely\n"
            "3. Re-enable Blender MCP addon\n"
            "4. Run this diagnostic again\n\n"
            "⚠️ DO NOT attempt any Blender operations until connection is restored!"
        )

    return diagnosis


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
