# Debug Traceback Template

This prompt template wraps recent terminal logs and error information into an AI-friendly format for analysis.

## Usage

Use this template when you encounter errors, exceptions, or unexpected behavior in Blender operations.

## Template

```
**🐛 DEBUG REQUEST: Blender Error Analysis**

**Context:**
- Operation: {{operation_description}}
- Blender Version: {{blender_version}}
- MCP Server: BPYMCP {{server_version}}
- Timestamp: {{timestamp}}

**Error Details:**
```
{{error_message}}
```

**Recent Terminal Output:**
```
{{terminal_logs}}
```

**Code That Failed:**
```python
{{failed_code}}
```

**Expected Behavior:**
{{expected_behavior}}

**Actual Behavior:**
{{actual_behavior}}

**Environment Info:**
- Python Version: {{python_version}}
- Active Scene: {{scene_name}}
- Active Object: {{active_object}}
- Addon State: {{addon_state}}

**Analysis Request:**
Please analyze this error and provide:
1. **Root Cause**: What specifically went wrong?
2. **Fix**: Exact code or steps to resolve the issue
3. **Prevention**: How to avoid this error in the future
4. **Alternative**: If the approach is flawed, suggest a better method

Focus on Blender-specific issues, Python API usage, and MCP communication problems.
```

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `operation_description` | What you were trying to do | "Creating a cube with custom material" |
| `blender_version` | Version from `bpy.app.version_string` | "4.2.0" |
| `server_version` | BPYMCP version | "0.1.0" |
| `timestamp` | When the error occurred | "2025-01-24 15:30:45" |
| `error_message` | The actual error/exception text | "AttributeError: 'NoneType' object has no attribute 'name'" |
| `terminal_logs` | Recent output from terminal/console | Last 50 lines of output |
| `failed_code` | The Python code that caused the error | Code snippet |
| `expected_behavior` | What should have happened | "A cube should appear at origin" |
| `actual_behavior` | What actually happened | "Nothing appeared, got error" |
| `python_version` | Python version in Blender | "3.11.7" |
| `scene_name` | Current scene name | "Scene" |
| `active_object` | Currently active object | "Cube" or "None" |
| `addon_state` | Status of relevant addons | "BPY MCP: Enabled, Custom Tools: Disabled" |

## Quick Fill Example

For rapid debugging, you can use this minimal version:

```
🐛 **Error**: {{error_message}}
📝 **Code**: {{failed_code}}
🎯 **Goal**: {{what_you_wanted}}
🔍 **Help**: Please fix this Blender issue
```
