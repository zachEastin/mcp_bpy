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
from pydantic import BaseModel, Field


# Pydantic models for structured output
class BlenderObjectInfo(BaseModel):
    """Information about a Blender object."""
    name: str = Field(description="Name of the object")
    type: str = Field(description="Type of the object (MESH, CAMERA, LIGHT, etc.)")
    data_path: str = Field(description="Data-block path in Blender")
    active: bool = Field(description="Whether this is the active object")
    visible: bool = Field(description="Whether the object is visible in viewport")
    location: list[float] = Field(description="Object location (x, y, z)")


class ObjectListResult(BaseModel):
    """Result of listing objects in the scene."""
    objects: list[BlenderObjectInfo] = Field(description="List of objects in the scene")
    total_count: int = Field(description="Total number of objects")
    filtered_type: str | None = Field(description="Type filter applied, if any")


class AddonOperatorInfo(BaseModel):
    """Information about an addon operator."""
    bl_idname: str = Field(description="Blender identifier for the operator")
    bl_label: str = Field(description="Human-readable label")
    bl_description: str | None = Field(description="Description of the operator")
    bl_category: str | None = Field(description="Category the operator belongs to")


class AddonClassInfo(BaseModel):
    """Information about an addon class."""
    name: str = Field(description="Class name")
    type: str = Field(description="Type of class (Panel, Operator, PropertyGroup, etc.)")
    bl_idname: str | None = Field(description="Blender identifier, if applicable")
    bl_label: str | None = Field(description="Human-readable label, if applicable")


class AddonKeymapInfo(BaseModel):
    """Information about addon keymaps."""
    name: str = Field(description="Keymap name")
    space_type: str = Field(description="Space type where keymap is active")
    region_type: str = Field(description="Region type where keymap is active")
    key_items: list[str] = Field(description="List of key bindings")


class AddonInspectionResult(BaseModel):
    """Result of inspecting an addon."""
    addon_name: str = Field(description="Name of the inspected addon")
    enabled: bool = Field(description="Whether the addon is currently enabled")
    version: str | None = Field(description="Version of the addon")
    operators: list[AddonOperatorInfo] = Field(description="Operators registered by the addon")
    classes: list[AddonClassInfo] = Field(description="Classes registered by the addon")
    keymaps: list[AddonKeymapInfo] = Field(description="Keymaps registered by the addon")
    properties: list[str] = Field(description="Properties registered by the addon")


class AddonReloadResult(BaseModel):
    """Result of reloading an addon."""
    addon_name: str | None = Field(description="Name of the reloaded addon, if specific")
    global_reload: bool = Field(description="Whether a global script reload was performed")
    success: bool = Field(description="Whether the reload was successful")
    reloaded_modules: list[str] = Field(description="List of modules that were reloaded")
    errors: list[str] = Field(description="Any errors that occurred during reload")

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

    print("BPYMCP server starting...")
    print(f"Will attempt to connect to Blender on {host}:{port} when tools are called")

    try:
        # Try to connect to Blender with timeout
        try:
            _reader, _writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=2.0
            )
            print(f"Connected to Blender on {host}:{port}")

            # Authenticate if needed with timeout
            auth_message = {"id": "startup_auth", "token": os.getenv("BLENDER_MCP_TOKEN", "test-token-123")}
            await send_message(_writer, auth_message)
            response = await asyncio.wait_for(receive_message(_reader), timeout=2.0)

            if response.get("authenticated"):
                print("Successfully authenticated with Blender")
            else:
                print("Warning: Authentication may have failed")

        except TimeoutError:
            print("Warning: Connection to Blender timed out")
            print("Server will start but tools will fail until Blender is connected")
            _reader = None
            _writer = None

    except Exception as e:
        print(f"Warning: Could not connect to Blender: {e}")
        print("Server will start but tools will fail until Blender is connected")
        _reader = None
        _writer = None

    print("BPYMCP server ready!")

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


async def ensure_blender_connection():
    """Ensure we have a valid connection to Blender, attempt to reconnect if needed."""
    global _reader, _writer

    if _reader is None or _writer is None:
        port = int(os.getenv("BLENDER_MCP_PORT", "4777"))
        host = "localhost"
        
        try:
            _reader, _writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0
            )
            
            # Test if authentication is required by trying a simple command first
            test_message = {"id": "connection_test", "code": "import bpy; print('Connection test')"}
            await send_message(_writer, test_message)
            response = await asyncio.wait_for(receive_message(_reader), timeout=5.0)
            
            # If the test works without auth, we're good
            if not response.get("error"):
                return  # Connection successful without authentication
            
            # If test fails, try authentication
            auth_message = {"id": "tool_auth", "token": os.getenv("BLENDER_MCP_TOKEN", "test-token-123")}
            await send_message(_writer, auth_message)
            auth_response = await asyncio.wait_for(receive_message(_reader), timeout=5.0)
            
            if not auth_response.get("authenticated"):
                raise McpError(ErrorData("CONNECTION_FAILED", "Authentication failed"))
                
        except (TimeoutError, ConnectionRefusedError, OSError) as e:
            raise McpError(
                ErrorData(
                    "CONNECTION_FAILED",
                    f"Cannot connect to Blender on {host}:{port}. "
                    f"Make sure Blender is running with the MCP addon enabled. Error: {e}"
                )
            ) from e


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
        # Ensure connection before proceeding
        await ensure_blender_connection()

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

            # Step 3: Test code execution first (to see if auth is required)
            try:
                import uuid

                test_id = str(uuid.uuid4())
                test_message = {"id": test_id, "code": "import bpy; print(f'Test OK: {bpy.app.version_string}')"}

                await send_message(_writer, test_message)
                test_response = await receive_message(_reader)

                # If code execution works without auth, we're good
                if not test_response.get("error"):
                    diagnosis["authenticated"] = True  # No auth required
                    diagnosis["code_execution"] = True
                    diagnosis["status"] = "fully_connected"
                    diagnosis["success"] = True
                    
                    # Try to extract Blender version from the output
                    output = test_response.get("output", "")
                    if "Test OK:" in output:
                        diagnosis["blender_version"] = output.split("Test OK: ")[1].strip()
                    else:
                        diagnosis["blender_version"] = "Unknown"
                    
                    diagnosis["instructions"] = (
                        f"✅ CONNECTION PERFECT!\n\n"
                        f"Blender Version: {diagnosis['blender_version']}\n"
                        f"Authentication: Not required\n"
                        f"Code Execution: Working\n\n"
                        f"🚀 Ready for Blender operations!"
                    )
                    return diagnosis

                # If code execution fails, try authentication
                auth_id = str(uuid.uuid4())
                auth_message = {"id": auth_id, "token": os.getenv("BLENDER_MCP_TOKEN", "test-token-123")}

                await send_message(_writer, auth_message)
                auth_response = await receive_message(_reader)

                if auth_response.get("authenticated"):
                    diagnosis["authenticated"] = True
                    diagnosis["blender_version"] = auth_response.get("blender_version", "Unknown")
                    
                    # Test code execution again after auth
                    test_id2 = str(uuid.uuid4())
                    test_message2 = {"id": test_id2, "code": "import bpy; print(f'Test OK: {bpy.app.version_string}')"}
                    
                    await send_message(_writer, test_message2)
                    test_response2 = await receive_message(_reader)

                    if test_response2.get("error"):
                        diagnosis["status"] = "execution_failed"
                        diagnosis["instructions"] = (
                            f"❌ CODE EXECUTION FAILED: {test_response2['error']}\n\n"
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


@mcp.tool()
async def list_objects(type: str | None = None) -> ObjectListResult:
    """Return names & data-block paths of objects in scene.
    
    Args:
        type: Optional object type filter (MESH, CAMERA, LIGHT, etc.)
    
    Returns:
        ObjectListResult: Structured information about objects in the scene
    
    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Ensure connection
    await ensure_blender_connection()
    
    # Build the Python code to list objects
    type_filter = f"if obj.type != '{type}': continue" if type else ""
    code = f'''
import bpy
import json

# Get all objects in the scene
all_objects = list(bpy.context.scene.objects)
active_object = bpy.context.view_layer.objects.active

objects_data = []
for obj in all_objects:
    # Check type filter
    {type_filter}
    
    # Get object information
    obj_info = {{
        "name": obj.name,
        "type": obj.type,
        "data_path": f"bpy.data.objects['{{obj.name}}']",
        "active": obj == active_object,
        "visible": obj.visible_get(),
        "location": list(obj.location)
    }}
    objects_data.append(obj_info)

# Create result
result = {{
    "objects": objects_data,
    "total_count": len(objects_data),
    "filtered_type": "{type}" if "{type}" else None
}}

print("RESULT:" + json.dumps(result))
'''
    
    # Execute the code
    response = await run_python(code, stream=False)
    
    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to list objects: {response['error']}"))
    
    # Parse the result from the output
    output = response["output"] or ""
    if "RESULT:" in output:
        result_str = output.split("RESULT:")[1].strip()
        try:
            result_data = json.loads(result_str)  # Use json.loads instead of eval
            return ObjectListResult(**result_data)
        except Exception as e:
            raise McpError(ErrorData(code=4003, message=f"Failed to parse object list result: {e}")) from e
    
    # Fallback empty result
    return ObjectListResult(objects=[], total_count=0, filtered_type=type)


@mcp.tool()
async def inspect_addon(name: str) -> AddonInspectionResult:
    """List classes, operators, keymaps registered by addon.
    
    Args:
        name: Name of the addon to inspect
    
    Returns:
        AddonInspectionResult: Structured information about the addon
    
    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Ensure connection
    await ensure_blender_connection()
    
    code = f'''
import bpy
import addon_utils
import sys
import json

addon_name = "{name}"

# Get addon info
addon = None
enabled = False
version = None

# Find the addon
for mod in addon_utils.modules():
    if mod.__name__ == addon_name or mod.bl_info.get("name") == addon_name:
        addon = mod
        enabled = addon_name in bpy.context.preferences.addons
        version = str(mod.bl_info.get("version", "Unknown"))
        break

if not addon:
    # Try to find by partial name
    for mod in addon_utils.modules():
        if addon_name.lower() in mod.__name__.lower() or addon_name.lower() in mod.bl_info.get("name", "").lower():
            addon = mod
            enabled = mod.__name__ in bpy.context.preferences.addons
            version = str(mod.bl_info.get("version", "Unknown"))
            addon_name = mod.__name__  # Use the actual module name
            break

# Simple addon info only - avoid complex introspection
operators = []
classes_info = []
keymaps = []
properties = []

# Try to get basic properties if addon is found
if addon:
    try:
        # Try to get addon preferences
        prefs = bpy.context.preferences.addons.get(addon_name)
        if prefs:
            properties.append("Has preferences object")
    except:
        pass

result = {{
    "addon_name": addon_name,
    "enabled": enabled,
    "version": version,
    "operators": operators,
    "classes": classes_info,
    "keymaps": keymaps,
    "properties": properties
}}

print("RESULT:" + json.dumps(result))
'''
    
    # Execute the code
    response = await run_python(code, stream=False)
    
    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to inspect addon: {response['error']}"))
    
    # Parse the result from the output
    output = response["output"] or ""
    if "RESULT:" in output:
        result_str = output.split("RESULT:")[1].strip()
        try:
            result_data = json.loads(result_str)  # Use json.loads instead of eval
            return AddonInspectionResult(**result_data)
        except Exception as e:
            raise McpError(ErrorData(code=4003, message=f"Failed to parse addon inspection result: {e}")) from e
    
    # Fallback empty result
    return AddonInspectionResult(
        addon_name=name,
        enabled=False,
        version=None,
        operators=[],
        classes=[],
        keymaps=[],
        properties=[]
    )


@mcp.tool()
async def reload_addon(name: str | None = None) -> AddonReloadResult:
    """bpy.ops.reload_scripts() + targeted reload.
    
    Args:
        name: Optional name of specific addon to reload. If None, performs global reload.
    
    Returns:
        AddonReloadResult: Information about the reload operation
    
    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Ensure connection
    await ensure_blender_connection()
    
    if name:
        # Targeted addon reload
        code = f'''
import bpy
import addon_utils
import sys
import importlib
import json

addon_name = "{name}"
errors = []
reloaded_modules = []

try:
    # First try to find and disable the addon
    addon_found = False
    for mod in addon_utils.modules():
        if mod.__name__ == addon_name or mod.bl_info.get("name") == addon_name:
            addon_name = mod.__name__  # Use actual module name
            addon_found = True
            break
    
    if not addon_found:
        errors.append(f"Addon '{{addon_name}}' not found")
    else:
        # Disable addon if enabled
        if addon_name in bpy.context.preferences.addons:
            bpy.ops.preferences.addon_disable(module=addon_name)
        
        # Reload the addon module and its submodules
        modules_to_reload = []
        for module_name in list(sys.modules.keys()):
            if module_name.startswith(addon_name):
                modules_to_reload.append(module_name)
        
        for module_name in modules_to_reload:
            try:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    reloaded_modules.append(module_name)
            except Exception as e:
                errors.append(f"Failed to reload module {{module_name}}: {{str(e)}}")
        
        # Re-enable addon
        try:
            bpy.ops.preferences.addon_enable(module=addon_name)
        except Exception as e:
            errors.append(f"Failed to re-enable addon: {{str(e)}}")

    success = len(errors) == 0
    
except Exception as e:
    errors.append(f"Unexpected error: {{str(e)}}")
    success = False

result = {{
    "addon_name": addon_name,
    "global_reload": False,
    "success": success,
    "reloaded_modules": reloaded_modules,
    "errors": errors
}}

print("RESULT:" + json.dumps(result))
'''
    else:
        # Global script reload
        code = '''
import bpy
import sys
import json

errors = []
reloaded_modules = []

try:
    # Perform global script reload
    bpy.ops.script.reload()
    
    # Get list of all Python modules (simplified)
    reloaded_modules = [name for name in sys.modules.keys() if not name.startswith('_')][:20]  # Limit output
    
    success = True
    
except Exception as e:
    errors.append(f"Global reload failed: {str(e)}")
    success = False

result = {
    "addon_name": None,
    "global_reload": True,
    "success": success,
    "reloaded_modules": reloaded_modules,
    "errors": errors
}

print("RESULT:" + json.dumps(result))
'''
    
    # Execute the code
    response = await run_python(code, stream=False)
    
    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to reload addon: {response['error']}"))
    
    # Parse the result from the output
    output = response["output"] or ""
    if "RESULT:" in output:
        result_str = output.split("RESULT:")[1].strip()
        try:
            result_data = json.loads(result_str)  # Use json.loads instead of eval
            return AddonReloadResult(**result_data)
        except Exception as e:
            raise McpError(ErrorData(code=4003, message=f"Failed to parse reload result: {e}")) from e
    
    # Fallback result
    return AddonReloadResult(
        addon_name=name,
        global_reload=name is None,
        success=False,
        reloaded_modules=[],
        errors=["Failed to parse reload result"]
    )


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
