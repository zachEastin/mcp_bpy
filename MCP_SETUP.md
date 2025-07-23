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
         "cwd": "t:\\Coding_Projects\\mcp_bpy",
         "env": {}
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

## Testing

To test the server manually:

```bash
cd t:\Coding_Projects\mcp_bpy
uv run python -m bpy_mcp.server
```

Or use the configured script:

```bash
uv run bpy-mcp
```
