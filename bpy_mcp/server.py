"""FastMCP server for Blender Add-on management."""
from __future__ import annotations

import asyncio
import json
import os
import struct
import uuid

from typing import Any
from contextlib import asynccontextmanager

from mcp import McpError
from mcp.server.fastmcp import FastMCP
from mcp.types import ErrorData
from pydantic import BaseModel, Field



# Pydantic models for structured output
class BlenderAttributeGeneric(BaseModel):
    name: str = Field(description="Name of the attribute")
    domain: str = Field(description="Domain of the attribute")
    data_type: str = Field(description="Type of the attribute")
    length: int = Field(description="Length of the data of attribute, if applicable")
    is_internal: bool = Field(description="Whether the attribute is internal to Blender")
    is_required: bool = Field(description="Whether the attribute is required")

class BlenderObjectInfoResult(BaseModel):
    name: str = Field(description="Name of the object")
    type: str = Field(description="Type of the object (MESH, CAMERA, LIGHT, etc.)")
    data_path: str = Field(description="Data-block path in Blender")
    active: bool = Field(description="Whether this is the active object")
    visible: bool = Field(description="Whether the object is visible in viewport")
    location: list[float] | tuple[float, ...] = Field(description="Object location (x, y, z)")
    rotation: list[float] | tuple[float, ...] = Field(description="Object euler rotation (x, y, z)")
    scale: list[float] | tuple[float, ...] = Field(description="Object scale (x, y, z)")
    dimensions: list[float] | tuple[float, ...] = Field(description="Object dimensions (x, y, z)")
    material_slots: dict[str, dict[str, bool | str | None]] = Field(description="Dictionary of material slots, keyed by slot name")
    modifiers: list[str] = Field(description="List of modifiers")
    constraints: list[str] = Field(description="List of constraints")
    children: list[str] = Field(description="List of child objects")
    parent: str | None = Field(description="Name of the parent object, if any")
    vertex_groups: list[str] = Field(description="List of vertex groups")
    other_attributes: dict[str, Any] = Field(description="Other attributes of the object as requested")


class BlenderObjectInfoSimple(BaseModel):
    """Information about a Blender object."""
    name: str = Field(description="Name of the object")
    type: str = Field(description="Type of the object (MESH, CAMERA, LIGHT, etc.)")
    data_path: str = Field(description="Data-block path in Blender")
    active: bool = Field(description="Whether this is the active object")
    visible: bool = Field(description="Whether the object is visible in viewport")
    location: list[float] = Field(description="Object location (x, y, z)")


class BlenderObjectDataInfo(BaseModel):
    """Information about a Blender object's data."""
    name: str = Field(description="Name of the object")
    type: str = Field(description="Type of the object (MESH, CAMERA, LIGHT, etc.)")
    data_path: str = Field(description="Data-block path in Blender")
    attributes: dict[str, BlenderAttributeGeneric] = Field(description="Attributes of the object data-block")
    materials: list[str] = Field(description="List of material names applied to the object")
    other_attributes: dict[str, Any] = Field(description="Other attributes of the object as requested")


class ObjectListResult(BaseModel):
    """Result of listing objects in the scene."""
    objects: list[BlenderObjectInfoSimple] = Field(description="List of objects in the scene")
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


class NodeGroupSocketInfo(BaseModel):
    """Information about a node group socket."""
    type: str = Field(description="Socket type")
    description: str = Field(description="Socket description")
    identifier: str = Field(description="Socket identifier")
    name: str = Field(description="Socket name")
    default_value: Any | None = Field(description="Default value if applicable")


class NodeGroupInfo(BaseModel):
    """Information about a node group."""
    name: str = Field(description="Name of the node group")
    node_tree_type: str = Field(description="Type of the node tree")
    node_count: int = Field(description="Number of nodes in the group")
    inputs: list[NodeGroupSocketInfo] = Field(description="Input sockets")
    outputs: list[NodeGroupSocketInfo] = Field(description="Output sockets")


class NodeGroupListResult(BaseModel):
    """Result of listing node groups."""
    node_groups: list[NodeGroupInfo] = Field(description="List of node groups")
    total_count: int = Field(description="Total number of node groups")


class NodeSocketInfo(BaseModel):
    """Information about a node socket."""
    name: str = Field(description="Socket name")
    description: str = Field(description="Socket description")
    type: str = Field(description="Socket type")
    default_value: Any | None = Field(description="Default value if applicable and not linked")
    links: list[dict[str, Any]] = Field(description="Connected links")


class NodePropertyInfo(BaseModel):
    """Information about a node property."""
    name: str = Field(description="Property name")
    bl_rna_type: str = Field(description="Blender RNA type")
    value: Any = Field(description="Property value")


class NodeInfo(BaseModel):
    """Detailed information about a node."""
    name: str = Field(description="Node name")
    label: str = Field(description="Node label")
    bl_idname: str = Field(description="Blender identifier")
    use_custom_color: bool = Field(description="Whether node uses custom color")
    color: list[float] = Field(description="Node color (RGB)")
    location: list[float] = Field(description="Node location (x, y)")
    location_absolute: list[float] = Field(description="Absolute node location")
    mute: bool = Field(description="Whether node is muted")
    parent: str | None = Field(description="Parent frame node name if any")
    selection_status: bool = Field(description="Whether node is selected")
    inputs: list[NodeSocketInfo] = Field(description="Input sockets")
    outputs: list[NodeSocketInfo] = Field(description="Output sockets")
    properties: list[NodePropertyInfo] = Field(description="Node properties")
    node_tree: dict = Field(description="If node is a group node, this is the information of the node tree of that group. Returns empty if not a group.")


class NodeLinkInfo(BaseModel):
    """Information about a node link."""
    from_node: str = Field(description="Source node name")
    from_socket: dict[str, str] = Field(description="Source socket info")
    to_node: str = Field(description="Target node name")
    to_socket: dict[str, str] = Field(description="Target socket info")
    is_valid: bool = Field(description="Whether the link is valid")
    is_muted: bool = Field(description="Whether the link is muted")


class NodeGroupDetailResult(BaseModel):
    """Detailed result of node group information."""
    node_group_name: str = Field(description="Name of the node group")
    node_tree_type: str = Field(description="Type of the node tree")
    nodes: list[NodeInfo] = Field(description="Detailed node information")
    # links: list[NodeLinkInfo] = Field(description="Link information")
    total_nodes: int = Field(description="Total number of nodes")
    total_links: int = Field(description="Total number of links")

# Rebuild models to resolve forward references
NodeInfo.model_rebuild()
NodeLinkInfo.model_rebuild()
NodeGroupDetailResult.model_rebuild()

class OperatorPropertyInfo(BaseModel):
    """Information about an operator property."""
    name: str = Field(description="Property name")
    type: str = Field(description="Property type (StringProperty, BoolProperty, etc.)")
    description: str = Field(description="Property description")
    default: str | None = Field(description="Default value as string")
    options: list[str] = Field(description="Property options (e.g., HIDDEN, ANIMATABLE)")


class OperatorGenerationRequest(BaseModel):
    """Request parameters for generating a Blender operator."""
    name: str = Field(description="Human-readable name of the operator (e.g., 'Add Cube')")
    description: str = Field(description="Description of what the operator does")
    category: str = Field(
        description="Category for the operator (e.g., 'MESH', 'OBJECT', 'CUSTOM')",
        default="OBJECT"
    )
    include_invoke: bool = Field(
        description="Whether to include invoke() method", default=False
    )
    include_poll: bool = Field(
        description="Whether to include poll() method", default=False
    )
    include_modal: bool = Field(
        description="Whether to include modal() method for interactive operators",
        default=False
    )
    properties: list[OperatorPropertyInfo] = Field(
        description="List of properties for the operator", default_factory=list
    )
    output_file: str | None = Field(
        description="Optional output file path. If None, will be written to current workspace",
        default=None
    )


class OperatorGenerationResult(BaseModel):
    """Result of operator generation."""
    success: bool = Field(description="Whether generation was successful")
    file_path: str = Field(description="Path where the operator was written")
    class_name: str = Field(description="Generated class name")
    bl_idname: str = Field(description="Generated bl_idname")
    operator_code: str = Field(description="Generated operator code")
    registration_code: str = Field(description="Generated registration code")
    errors: list[str] = Field(description="Any errors encountered", default_factory=list)
    warnings: list[str] = Field(description="Any warnings", default_factory=list)

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
                raise McpError(ErrorData(code=4001, message="Authentication failed"))
                
        except (TimeoutError, ConnectionRefusedError, OSError) as e:
            raise McpError(
                ErrorData(
                    code=4000,
                    message=f"Cannot connect to Blender on {host}:{port}. "
                    f"Make sure Blender is running with the MCP addon enabled. Error: {e}"
                )
            ) from e


async def send_handler_message(handler_name: str, params: dict | None = None) -> dict[str, Any]:
    """Send a handler message to Blender and return the result.

    Args:
        handler_name: The name of the handler to execute
        params: Optional parameters to pass to the handler

    Returns:
        dict: Handler execution result with 'output', 'error', and 'result' keys

    Raises:
        McpError: If not connected to Blender or execution fails
    """
    global _reader, _writer

    async with _connection_lock:
        # Ensure connection before proceeding
        await ensure_blender_connection()

        try:
            # Generate unique message ID
            message_id = str(uuid.uuid4())

            # Send handler request
            message = {
                "id": message_id,
                "handler": handler_name,
                "params": params or {}
            }

            await send_message(_writer, message)  # type: ignore

            # Handle response
            response = await receive_message(_reader)  # type: ignore

            # Check for errors in response
            if response.get("error"):
                raise McpError(ErrorData(code=4002, message=response["error"]))

            # Return the response (includes output, error, and result)
            return {
                "output": response.get("output", ""),
                "error": response.get("error"),
                "result": response.get("result")
            }

        except TimeoutError as e:
            raise McpError(ErrorData(code=4003, message="Timeout waiting for Blender response")) from e
        except ConnectionError as e:
            raise McpError(ErrorData(code=4004, message=f"Connection to Blender lost: {e}")) from e
        except Exception as e:
            raise McpError(ErrorData(code=4000, message=f"Unexpected error communicating with Blender: {e}")) from e


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

    IMPORTANT: Code executes in a RESTRICTED ENVIRONMENT for security.

    AVAILABLE BUILT-INS:
    - Standard types: str, int, float, bool, list, dict, tuple, set
    - Iterators: range, enumerate, zip, sorted, reversed
    - Math/logic: min, max, sum, any, all, len
    - Introspection: dir, vars, hasattr, getattr, isinstance, type
    - Error handling: Exception, ValueError, TypeError, AttributeError, KeyError,
      IndexError, RuntimeError, NotImplementedError, StopIteration
    - I/O: print (output captured and returned)
    - Imports: __import__ (allows importing modules)
    - Scope access: globals(), locals() (returns safe globals only)

    AVAILABLE MODULES:
    - bpy: Full Blender Python API
    - bmesh: Blender mesh editing utilities
    - mathutils: Blender math utilities (Vector, Matrix, etc.)

    RESTRICTED/FORBIDDEN:
    - File operations: open, file
    - Code execution: eval, exec, compile
    - User interaction: input, raw_input
    - Process control: exit, quit
    - System access: help, credits, license, copyright
    - Attribute manipulation: delattr, setattr
    - Module reloading: reload
    - Internal Python objects: __loader__, __spec__, __package__

    SECURITY NOTES:
    - Code runs in Blender's main thread - avoid long-running operations
    - stdout is captured and returned in the 'output' field
    - Use try/except blocks for error handling as exceptions are caught
    - Import statements work normally within the restricted environment

    EXAMPLES:
    ```python
    # List all mesh objects
    meshes = [obj.name for obj in bpy.data.objects if obj.type == 'MESH']
    print(f"Found {len(meshes)} mesh objects: {meshes}")

    # Create a new cube
    bpy.ops.mesh.primitive_cube_add()
    print(f"Active object: {bpy.context.active_object.name}")

    # Use bmesh for mesh operations
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    ```

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
            message_id = str(uuid.uuid4())

            # Send code execution request
            message = {"id": message_id, "code": code, "stream": stream}

            await send_message(_writer, message)  # type: ignore

            if stream:
                # Handle streaming responses
                output_chunks = []

                while True:
                    response = await receive_message(_reader)  # type: ignore

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
                response = await receive_message(_reader)  # type: ignore

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
async def list_objects(only_view_layer: bool = False, type: str | None = None) -> ObjectListResult:
    """Return names & data-block paths of objects in scene.

    Args:
        only_view_layer: If True, only include objects in the view_layer
        type: Optional object type filter (MESH, CAMERA, LIGHT, etc.)
        other_attributes: Optional list of other attributes to include. Must be attributes to be called directly on `bpy.types.Object`.

    Returns:
        ObjectListResult: Structured information about objects in the scene

    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Send handler message to Blender
    response = await send_handler_message(
        "list_objects",
        {"only_view_layer": only_view_layer, "type": type}
    )

    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to list objects: {response['error']}"))

    # Return structured result
    result_data = response.get("result")
    if result_data:
        return ObjectListResult(**result_data)

    # Fallback empty result
    return ObjectListResult(objects=[], total_count=0, filtered_type=type)


@mcp.tool()
async def get_object_info(object_name: str, get_as_evaluated: bool = False, other_attributes: list[str] | None = None) -> BlenderObjectInfoResult:
    """Return information about a specific object in the scene.

    Args:
        object_name: Name of the object to retrieve information for
        get_as_evaluated: If True, return evaluated data-blocks (useful to get the result of modifiers)
        other_attributes: Optional list of other attributes to include. Must be attributes to be called directly on `bpy.types.Object`.

    Returns:
        ObjectInfoResult: Structured information about the object in the scene

    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Send handler message to Blender
    response = await send_handler_message(
        "get_object_info",
        {"object_name": object_name, "get_as_evaluated": get_as_evaluated, "other_attributes": other_attributes}
    )

    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to get object info: {response['error']}"))

    # Return structured result
    result_data = response.get("result")
    if result_data:
        return BlenderObjectInfoResult(**result_data)

    # Fallback empty result
    return BlenderObjectInfoResult(
        name="UNKNOWN",
        type="UNKNOWN",
        data_path="",
        active=False,
        visible=False,
        location=(0.0, 0.0, 0.0),
        rotation=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        dimensions=(0.0, 0.0, 0.0),
        material_slots={},
        modifiers=[],
        constraints=[],
        children=[],
        parent=None,
        vertex_groups=[],
        other_attributes={}
    )


@mcp.tool()
async def get_object_data_info(object_name: str, get_as_evaluated: bool = False, other_attributes: list[str] | None = None) -> BlenderObjectDataInfo:
    """Return information about a specific object's data

    Args:
        object_name: Name of the object to retrieve information for
        get_as_evaluated: If True, return evaluated data-blocks (useful to get the result of modifiers)
        other_attributes: Optional list of other attributes to include. Must be attributes to be called directly on `bpy.types.Mesh`, `bpy.types.Curve`, etc.

    Returns:
        BlenderObjectDataInfo: Structured information about the object's data

    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Send handler message to Blender
    response = await send_handler_message(
        "get_object_data_info",
        {"object_name": object_name, "get_as_evaluated": get_as_evaluated, "other_attributes": other_attributes}
    )

    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to get object info: {response['error']}"))

    # Return structured result
    result_data = response.get("result")
    if result_data:
        return BlenderObjectDataInfo(**result_data)

    # Fallback empty result
    return BlenderObjectDataInfo(
        name="UNKNOWN",
        type="UNKNOWN",
        data_path="",
        attributes={},
        materials=[],
        other_attributes={}
    )


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
    # Send handler message to Blender
    response = await send_handler_message("inspect_addon", {"name": name})

    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to inspect addon: {response['error']}"))

    # Return structured result
    result_data = response.get("result")
    if result_data:
        return AddonInspectionResult(**result_data)

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
    # Send handler message to Blender
    response = await send_handler_message("reload_addon", {"name": name})

    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to reload addon: {response['error']}"))

    # Return structured result
    result_data = response.get("result")
    if result_data:
        return AddonReloadResult(**result_data)

    # Fallback result
    return AddonReloadResult(
        addon_name=name,
        global_reload=name is None,
        success=False,
        reloaded_modules=[],
        errors=["Failed to parse reload result"]
    )


@mcp.tool()
async def list_node_groups() -> NodeGroupListResult:
    """List all node trees (a.k.a. node groups) from bpy.data.node_groups.
    
    For each node group, returns name, node_tree_type, node_count, and 
    detailed information about inputs and outputs including type, description,
    identifier, and default_value if applicable.

    Returns:
        NodeGroupListResult: Structured information about all node groups

    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Send handler message to Blender
    response = await send_handler_message("list_node_groups", {})

    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to list node groups: {response['error']}"))

    # Return structured result
    result_data = response.get("result")
    if result_data:
        return NodeGroupListResult(**result_data)

    # Fallback result
    return NodeGroupListResult(
        node_groups=[],
        total_count=0
    )


@mcp.tool()
async def get_node_group_info(name: str) -> NodeGroupDetailResult:
    """Return a detailed, structured representation of a node group suitable for complex groups.

    For each node in the group, includes name, label, bl_idname, use_custom_color, color,
    location, location_absolute, mute, parent, selection_status, and detailed socket and
    property information. Also includes comprehensive link information.

    Args:
        name: Name of the node group to get detailed information for

    Returns:
        NodeGroupDetailResult: Detailed structured information about the node group

    Raises:
        McpError: If not connected to Blender or execution fails
    """
    # Send handler message to Blender
    response = await send_handler_message("get_node_group_info", {"name": name})

    if response["error"]:
        raise McpError(ErrorData(code=4002, message=f"Failed to get node group info: {response['error']}"))

    # Return structured result
    result_data = response.get("result")
    if result_data:
        return NodeGroupDetailResult(**result_data)

    # Fallback result
    return NodeGroupDetailResult(
        node_group_name=name,
        node_tree_type="UNKNOWN",
        nodes=[],
        # links=[],
        total_nodes=0,
        total_links=0
    )


@mcp.tool()
async def create_bpy_operator(
    name: str,
    description: str,
    category: str = "OBJECT",
    include_invoke: bool = False,
    include_poll: bool = False,
    include_modal: bool = False,
    properties: list[dict] | None = None,
    output_file: str | None = None
) -> OperatorGenerationResult:
    """Generate Blender operator boilerplate code.

    Creates a complete Blender operator class with proper bl_idname, bl_label,
    and execute() method. This tool runs entirely on the IDE side and does not
    require a connection to Blender.

    For more information about Blender operators, see:
    - https://docs.blender.org/api/current/bpy.types.Operator.html
    - https://docs.blender.org/api/current/bpy.ops.html

    Args:
        name: Human-readable name of the operator (e.g., 'Add Cube')
        description: Description of what the operator does
        category: Category for the operator (e.g., 'MESH', 'OBJECT', 'CUSTOM')
        include_invoke: Whether to include invoke() method
        include_poll: Whether to include poll() method
        include_modal: Whether to include modal() method for interactive operators
        properties: List of property dicts with keys: name, type, description, default, options
        output_file: Optional output file path. If None, creates in current workspace

    Returns:
        OperatorGenerationResult: Information about the generated operator

    Raises:
        McpError: If generation fails or validation errors occur
    """
    import re
    from pathlib import Path

    errors = []
    warnings = []

    try:
        # Validate inputs
        if not name or not name.strip():
            errors.append("Operator name cannot be empty")
        if not description or not description.strip():
            errors.append("Operator description cannot be empty")

        if errors:
            return OperatorGenerationResult(
                success=False,
                file_path="",
                class_name="",
                bl_idname="",
                operator_code="",
                registration_code="",
                errors=errors,
                warnings=warnings
            )

        # Generate class name from operator name
        # Convert "Add Cube" -> "AddCube"
        class_name = "".join(word.capitalize() for word in re.findall(r'\w+', name))
        class_name = f"{class_name}Operator"

        # Generate bl_idname from operator name
        # Convert "Add Cube" -> "mesh.add_cube" or "object.add_cube"
        idname_suffix = "_".join(re.findall(r'\w+', name.lower()))
        category_prefix = category.lower() if category else "object"
        bl_idname = f"{category_prefix}.{idname_suffix}"

        # Generate properties code
        properties_code = ""
        properties_imports = set()
        if properties:
            prop_lines = []
            for prop in properties:
                prop_name = prop.get("name", "")
                prop_type = prop.get("type", "StringProperty")
                prop_desc = prop.get("description", "")
                prop_default = prop.get("default")
                prop_options = prop.get("options", [])

                if not prop_name:
                    warnings.append(f"Skipping property with empty name: {prop}")
                    continue

                # Add import for property type
                properties_imports.add(prop_type)

                # Build property definition
                prop_line = f'    {prop_name}: {prop_type}('
                prop_args = []
                
                if prop_desc:
                    prop_args.append(f'name="{prop_desc}"')
                    prop_args.append(f'description="{prop_desc}"')
                
                if prop_default is not None:
                    if prop_type in ["StringProperty"]:
                        prop_args.append(f'default="{prop_default}"')
                    elif prop_type in ["BoolProperty"]:
                        prop_args.append(f'default={str(prop_default).capitalize()}')
                    elif prop_type in ["IntProperty", "FloatProperty"]:
                        prop_args.append(f'default={prop_default}')
                
                if prop_options:
                    options_str = "{" + ", ".join(f'"{opt}"' for opt in prop_options) + "}"
                    prop_args.append(f'options={options_str}')

                prop_line += ", ".join(prop_args) + ")"
                prop_lines.append(prop_line)

            if prop_lines:
                properties_code = "\n\n    # Operator properties\n" + "\n".join(prop_lines)

        # Generate method stubs
        invoke_method = ""
        if include_invoke:
            invoke_method = '''
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Invoke the operator.
        
        Called when the operator is invoked by the user.
        """
        # TODO: Implement invoke logic here
        return self.execute(context)'''

        poll_method = ""
        if include_poll:
            poll_method = '''
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Check if the operator can be executed.
        
        Returns:
            bool: True if the operator can be executed, False otherwise
        """
        # TODO: Implement poll logic here
        return True'''

        modal_method = ""
        if include_modal:
            modal_method = '''
    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Handle modal interaction.
        
        Called repeatedly while the operator is running in modal mode.
        """
        # TODO: Implement modal logic here
        if event.type in {'LEFTMOUSE'}:
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}'''

        # Generate complete operator code
        imports_section = "import bpy\nfrom bpy.types import Operator"
        if properties_imports:
            props_import = ", ".join(sorted(properties_imports))
            imports_section += f"\nfrom bpy.props import {props_import}"

        operator_code = f'''{imports_section}


class {class_name}(Operator):
    """{description}."""
    
    bl_idname = "{bl_idname}"
    bl_label = "{name}"
    bl_description = "{description}"
    bl_options = {{'REGISTER', 'UNDO'}}{properties_code}{poll_method}{invoke_method}

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Execute the operator.
        
        Args:
            context: Blender context
            
        Returns:
            set[str]: Execution result ({'FINISHED'}, {'CANCELLED'}, etc.)
        """
        # TODO: Implement your operator logic here
        self.report({{'INFO'}}, "{name} executed successfully")
        return {{'FINISHED'}}{modal_method}'''

        # Generate registration code
        registration_code = f'''

def register():
    """Register the operator."""
    bpy.utils.register_class({class_name})


def unregister():
    """Unregister the operator."""
    bpy.utils.unregister_class({class_name})


if __name__ == "__main__":
    register()'''

        # Combine operator and registration code
        full_code = operator_code + registration_code

        # Determine output file path
        if output_file is None:
            # Default to creating in current workspace
            workspace_path = Path.cwd()
            # Create an operators directory if it doesn't exist
            operators_dir = workspace_path / "operators"
            operators_dir.mkdir(exist_ok=True)
            output_file = str(operators_dir / f"{idname_suffix}_operator.py")
        else:
            output_file = str(Path(output_file).resolve())

        # Write the file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_code)
        except Exception as e:
            errors.append(f"Failed to write file: {e}")
            return OperatorGenerationResult(
                success=False,
                file_path=output_file,
                class_name=class_name,
                bl_idname=bl_idname,
                operator_code=operator_code,
                registration_code=registration_code,
                errors=errors,
                warnings=warnings
            )

        return OperatorGenerationResult(
            success=True,
            file_path=output_file,
            class_name=class_name,
            bl_idname=bl_idname,
            operator_code=operator_code,
            registration_code=registration_code,
            errors=errors,
            warnings=warnings
        )

    except Exception as e:
        errors.append(f"Unexpected error during operator generation: {e}")
        return OperatorGenerationResult(
            success=False,
            file_path="",
            class_name="",
            bl_idname="",
            operator_code="",
            registration_code="",
            errors=errors,
            warnings=warnings
        )


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
