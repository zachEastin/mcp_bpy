# Blender Add-on MCP Server

A Model Context Protocol (MCP) server for managing Blender add-ons and automation. This project provides both an MCP server for external integration and a Blender extension for in-application command execution.

## Features

### MCP Server (`bpy_mcp`)
- **Blender Communication**: Send Python commands to running Blender instances
- **Connection Management**: Check Blender server status and connectivity
- **Code Examples**: Get ready-to-use Blender automation examples
- **Error Handling**: Comprehensive error reporting and troubleshooting

### Blender Extension (`bpy_mcp_addon`)
- **Network Interface**: TCP server on localhost:4777 for command execution
- **Authentication**: Optional token-based security
- **Secure Execution**: Sandboxed Python environment
- **Real-time Communication**: JSON-based request/response protocol
- **Blender Integration**: Full access to bpy, bmesh, and mathutils APIs

## Quick Start

### 1. Install and Test MCP Server

```bash
git clone <repository-url>
cd mcp_bpy
uv sync

# Test the MCP server
uv run mcp dev bpy_mcp/server.py
```

### 2. Install Blender Extension

1. Copy `bpy_mcp_addon/` directory to your Blender extensions folder
2. Open Blender Preferences > Add-ons
3. Find and enable "BPY MCP" in the Development category
4. Configure network settings and start the server

### 3. Test Integration

```bash
# Test connection to Blender
cd tests/manual
python test_listener.py
```

## Usage Examples

### Using MCP Tools

```python
# In VS Code with MCP integration
@mcp.tool()
async def send_blender_command(code: str) -> dict:
    # Send Python code to running Blender instance
    result = await send_blender_command(
        code="bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))"
    )
    return result
```

### Direct Blender Communication

```python
# Create objects in Blender
await send_blender_command("""
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
bpy.context.object.name = "MyCube"
print(f"Created: {bpy.context.object.name}")
""")

# Get scene information
await send_blender_command("""
scene_info = {
    'name': bpy.context.scene.name,
    'frame': bpy.context.scene.frame_current,
    'objects': len(bpy.context.scene.objects)
}
print(f"Scene: {scene_info}")
""")
```

## Project Structure

```
bpy_mcp/
├── bpy_mcp/              # MCP server package
│   ├── __init__.py
│   ├── server.py         # Main MCP server with Blender tools
│   └── __main__.py
├── bpy_mcp_addon/        # Blender extension
│   ├── blender_manifest.toml  # Blender 4.2+ extension manifest
│   ├── __init__.py       # Extension registration and UI
│   ├── listener.py       # TCP server and command execution
│   └── README.md         # Extension documentation
├── tests/                # Test suite
│   ├── manual/           # Manual testing utilities
│   └── test_server.py    # Automated tests
└── .github/              # CI/CD workflows
```

## Development Setup

This project uses `uv` for dependency management and follows strict coding standards.

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Blender 4.2+ (for extension testing)

### Installation

```bash
git clone <repository-url>
cd mcp_bpy
uv sync
```

### Development Commands

```bash
# Run the MCP server
uv run mcp dev bpy_mcp/server.py

# Run tests
uv run pytest

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run pyright
```

## Architecture

### Communication Flow

1. **External Tool** (VS Code, AI Assistant) → **MCP Server** (`bpy_mcp`)
2. **MCP Server** → **TCP Connection** → **Blender Extension** (`bpy_mcp_addon`)
3. **Blender Extension** → **Python Execution** → **Blender APIs** (`bpy`, `bmesh`, etc.)
4. **Response** flows back through the same chain

### Security Model

- **Network Binding**: Server binds only to localhost by default
- **Authentication**: Optional token-based authentication
- **Sandboxed Execution**: Restricted Python environment in Blender
- **Permission Checks**: Respects Blender's network access settings

## Configuration

### MCP Server

Configure in VS Code settings or MCP configuration:

```json
{
  "mcpServers": {
    "bpy-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "bpy_mcp.server"],
      "cwd": "/path/to/mcp_bpy"
    }
  }
}
```

### Blender Extension

Configure in Blender Preferences > Add-ons > BPY MCP:
- **Host**: Network interface (default: localhost)
- **Port**: TCP port (default: 4777)
- **Authentication**: Enable/disable token authentication
- **Auto Start**: Start server when Blender launches

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if Blender is running with BPY MCP extension enabled
   - Verify network settings and port configuration
   - Ensure Blender's online access is enabled

2. **Authentication Failed**
   - Check authentication token in both server and extension
   - Verify token authentication settings

3. **Import Errors**
   - Blender `bpy` module is only available within Blender
   - Use manual test scripts to verify functionality

### Getting Help

- Check the Blender console for error messages
- Review extension logs in Blender preferences
- Use manual test utilities in `tests/manual/`

## Standards

- Line length: 120 characters
- Python version: 3.12+
- Linting: Ruff
- Type checking: Pyright
- Testing: pytest
- Package management: uv only

## License

TBD
