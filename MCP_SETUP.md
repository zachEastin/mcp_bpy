# MCP Configuration for VS Code

This file provides configuration for connecting VS Code to the Blender MCP server.

## Setup Instructions

1. **Add to VS Code User Settings**:
   
   Open VS Code settings (Ctrl+,) and add this to your `settings.json`:

   ```json
   {
     "mcp.servers": {
       "bpy-mcp": {
         "command": "uv",
         "args": ["run", "python", "-m", "bpy_mcp.server"],
         "cwd": "t:\\Coding_Projects\\blender_dev_mcp\\mcp_bpy",
         "env": {
           "BLENDER_MCP_PORT": "4777",
           "BLENDER_MCP_TOKEN": "optional-token"
         }
       }
     }
   }
   ```

2. **Alternative: Use MCP Configuration File**:

   You can also reference the included `mcp_config.json` file in your VS Code MCP settings.

3. **Verify Connection**:

   Once configured, VS Code should be able to connect to the MCP server and use its tools in AI chat sessions.

## Available Tools

- `hello_blender`: A test tool that returns a greeting from the Blender MCP server
- `run_python`: Execute Python code in the attached Blender instance

## Environment Variables

- `BLENDER_MCP_PORT`: Port number for Blender listener (default: 4777)
- `BLENDER_MCP_TOKEN`: Authentication token for Blender connection (optional)

## VS Code Copilot Integration

With the above configuration, you can use the MCP tools directly in VS Code Copilot chat:

```
@workspace Can you create a cube in Blender using the run_python tool?
```

The assistant can then use:
```python
run_python(code="bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))")
```

## Testing

To test the server manually:

```bash
cd t:\Coding_Projects\blender_dev_mcp\mcp_bpy
uv run python -m bpy_mcp.server
```

Or use the configured script:

```bash
uv run bpy-mcp
```

## Troubleshooting

1. **Connection Issues**: 
   - Ensure Blender is running with BPY MCP extension enabled
   - Check that the port matches between VS Code config and Blender extension
   - Verify network access is enabled in Blender

2. **Authentication Failures**:
   - Check that the token matches between VS Code config and Blender extension
   - Ensure token authentication is enabled in Blender extension preferences

3. **Tool Not Available**:
   - Restart VS Code after configuration changes
   - Check VS Code's MCP server logs for connection errors
