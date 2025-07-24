# Streaming Output Documentation

## Overview

Phase 3 of the BPY MCP project introduces streaming output functionality, allowing long-running Blender operations to provide real-time feedback through incremental output chunks.

## Features

### Real-time Output Streaming
- Execute Python code in Blender with live stdout streaming
- Each `print()` statement generates an immediate chunk response
- Consolidates final output while providing real-time feedback

### Backward Compatibility
- Non-streaming mode (`stream=False`) works exactly as before
- Existing integrations remain unchanged
- Optional streaming activation per request

### Error Handling
- Streaming errors are properly propagated with MCP error codes
- Graceful handling of connection issues during streaming
- Comprehensive test coverage for error scenarios

## Protocol

### Streaming Request
```json
{
  "id": "unique-message-id",
  "code": "for i in range(3): print(f'Processing {i}')",
  "stream": true
}
```

### Streaming Response Sequence
```json
// Chunk 1
{
  "id": "unique-message-id",
  "chunk": "Processing 0",
  "stream_end": false
}

// Chunk 2
{
  "id": "unique-message-id", 
  "chunk": "Processing 1",
  "stream_end": false
}

// Chunk 3
{
  "id": "unique-message-id",
  "chunk": "Processing 2", 
  "stream_end": false
}

// Final response
{
  "id": "unique-message-id",
  "output": "",
  "error": null,
  "stream_end": true
}
```

### Non-streaming Response (Traditional)
```json
{
  "id": "unique-message-id",
  "output": "Processing 0\\nProcessing 1\\nProcessing 2\\n",
  "error": null,
  "stream_end": true
}
```

## Usage Examples

### MCP Tool Usage
```python
# Enable streaming for real-time output
result = await run_python("""
for i in range(5):
    print(f"Step {i}: Processing data...")
    # Simulate work
    import time
    time.sleep(0.5)
print("Processing complete!")
""", stream=True)

# Traditional non-streaming mode
result = await run_python("print('Hello World')", stream=False)
```

### Copilot Chat Integration
```
User: Run a long operation in Blender with streaming output
Assistant: I'll run a simulation with streaming output so you can see progress in real-time.

#mcp_bpy-mcp_run_python
code: |
  for i in range(10):
      print(f"Processing frame {i+1}/10...")
      # Simulate frame processing
      import time
      time.sleep(0.2)
  print("Rendering complete!")
stream: true
```

## Implementation Details

### Blender Listener (`listener.py`)
- **`execute_code_streaming()`**: Handles streaming execution with custom stdout capture
- **`StreamingCapture`**: Custom `io.StringIO` subclass that sends chunks immediately
- **`send_response()`**: Sends individual chunk responses over TCP connection
- **Protocol handling**: Modified message processing to support streaming flag

### MCP Server (`server.py`)  
- **Enhanced `run_python` tool**: Handles both streaming and non-streaming modes
- **Real-time display**: Shows `[STREAM]` prefixed output in console
- **Chunk consolidation**: Combines streaming chunks into final output
- **Error propagation**: Maintains MCP error codes for streaming failures

### Testing (`test_streaming.py`)
- **6 comprehensive test scenarios**: Basic, error, empty, large, compatibility, message ID
- **Mock streaming listener**: `FakeStreamingBlenderListener` for isolated testing
- **Async test support**: Uses `pytest-asyncio` for proper async testing
- **Edge case coverage**: Empty output, large output, error conditions

## Performance Considerations

### Streaming Benefits
- **Real-time feedback**: Users see progress immediately
- **Better UX**: Long operations feel more responsive  
- **Progress monitoring**: Can track operation status

### Overhead
- **Multiple messages**: Streaming requires more network round-trips
- **Buffer management**: Small performance cost for immediate output
- **Protocol complexity**: Slightly more complex message handling

### Recommendations
- Use streaming for operations > 2 seconds
- Use non-streaming for quick operations
- Consider output frequency when designing streaming code

## Error Handling

### MCP Error Codes
- **4001**: Not connected to Blender
- **4002**: Blender execution error (including streaming errors)
- **4003**: Timeout waiting for response
- **4004**: Connection lost during streaming
- **4000**: Unexpected errors

### Error Scenarios
```python
# Streaming error example
try:
    result = await run_python("print(undefined_variable)", stream=True)
except McpError as e:
    if e.data.code == 4002:
        print(f"Blender execution error: {e.data.message}")
```

## Configuration

### Environment Variables
- `BLENDER_MCP_PORT`: Port for Blender connection (default: 4777)
- `BLENDER_MCP_TOKEN`: Authentication token (optional)

### VS Code Settings
```json
{
  "mcp.servers": {
    "bpy-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "bpy_mcp.server"],
      "cwd": "path/to/mcp_bpy",
      "env": {
        "BLENDER_MCP_PORT": "4777",
        "BLENDER_MCP_TOKEN": "optional-token"
      }
    }
  }
}
```

## Testing

### Run Streaming Tests
```bash
# Run all streaming tests
uv run python -m pytest tests/test_streaming.py -v

# Run specific streaming test
uv run python -m pytest tests/test_streaming.py::test_streaming_basic_functionality -v

# Run all tests including streaming
uv run python -m pytest -v
```

### Manual Testing
```python
# Start Blender with BPY MCP extension enabled
# In MCP chat or tool interface:

#mcp_bpy-mcp_run_python
code: |
  import time
  for i in range(5):
      print(f"Processing step {i+1}/5...")
      time.sleep(0.5)
  print("Complete!")
stream: true
```

## Future Enhancements

### Planned Features
- **Progress percentages**: Report completion percentages for operations
- **Cancellation support**: Allow canceling streaming operations
- **Output buffering**: Configurable buffering strategies
- **Performance metrics**: Track streaming performance

### Potential Use Cases
- **Mesh processing**: Stream progress during complex mesh operations
- **Rendering**: Show frame-by-frame rendering progress
- **Animation**: Report keyframe processing status
- **Import/Export**: Display file processing progress

## Troubleshooting

### Common Issues

**Streaming not working**
- Verify Blender extension is enabled and server is running
- Check network connectivity on port 4777
- Ensure `stream=true` parameter is included

**Chunks not appearing in real-time**
- Blender may be buffering output - use `sys.stdout.flush()`
- Check for blocking operations between print statements

**Connection errors during streaming**
- Network interruption can break streaming
- Implement retry logic for critical operations
- Monitor connection status

### Debug Commands
```python
# Test basic connection
#mcp_bpy-mcp_hello_blender

# Test non-streaming first
#mcp_bpy-mcp_run_python
code: print("Hello World")
stream: false

# Test streaming with simple output
#mcp_bpy-mcp_run_python  
code: |
  for i in range(3):
      print(f"Test {i}")
stream: true
```
