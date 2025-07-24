# Blender MCP Diagnostic Tool

I've added a new MCP tool called `diagnose_connection` to help AI assistants check if the Blender connection is working properly.

## Tool: `diagnose_connection`

### Purpose
This tool performs comprehensive connection tests and provides specific instructions if issues are found. It should be used:
- Before performing complex Blender operations
- When connection issues are suspected
- As a first troubleshooting step

### What it checks
1. **Port availability** - Is Blender listening on port 4777?
2. **TCP connection** - Can we establish a network connection?
3. **Authentication** - Are we properly authenticated?
4. **Code execution** - Can we run Python code in Blender?

### Return format
```json
{
    "status": "fully_connected|port_closed|no_connection|auth_failed|execution_failed|communication_error",
    "port_open": true/false,
    "tcp_connected": true/false, 
    "authenticated": true/false,
    "code_execution": true/false,
    "blender_version": "4.5.0 Beta",
    "instructions": "Human-readable instructions for fixing issues",
    "success": true/false
}
```

### AI Assistant Usage
When an AI assistant encounters Blender connection issues, it should:

1. **First, run the diagnostic tool:**
   ```
   #mcp_bpy-mcp_diagnose_connection
   ```

2. **If `success: false`, follow the instructions exactly:**
   - DO NOT attempt any Blender operations
   - Tell the user to follow the provided instructions
   - Wait for user confirmation before proceeding

3. **Only proceed with Blender operations if `success: true`**

### Example Instructions Output

#### Port Closed:
```
❌ BLENDER NOT LISTENING: Port 4777 is not open.

REQUIRED ACTIONS:
1. Ensure Blender is running
2. In Blender: Edit > Preferences > Add-ons
3. Find 'BPY MCP' addon and enable it
4. If already enabled, disable and re-enable it
5. Check Blender console for 'BPY MCP: Server started' message
6. Then restart this MCP server (restart VS Code)

⚠️ DO NOT attempt any Blender operations until connection is restored!
```

#### Connection Success:
```
✅ CONNECTION PERFECT!

Blender Version: 4.5.0 Beta
Authentication: Working
Code Execution: Working

🚀 Ready for Blender operations!
```

## Usage Flow

1. AI detects potential connection issue OR wants to verify connection
2. AI runs `diagnose_connection` tool
3. If `success: false`, AI shows instructions to user and stops
4. If `success: true`, AI proceeds with Blender operations
5. If operations fail, AI reruns diagnostic and follows instructions

This ensures a robust connection workflow with clear troubleshooting steps.
