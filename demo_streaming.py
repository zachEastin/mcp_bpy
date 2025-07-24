#!/usr/bin/env python3
"""
Manual test script for streaming functionality.

This script demonstrates the streaming output feature by creating
a simple example that would show real-time output when connected
to a running Blender instance.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from bpy_mcp.server import run_python  # noqa: E402


async def demo_streaming():
    """Demonstrate streaming functionality with example code."""
    print("=== BPY MCP Streaming Demo ===")
    print("This demo requires Blender to be running with the BPY MCP extension enabled.")
    print()

    # Example 1: Basic streaming output
    print("Example 1: Basic streaming output")
    print("Code to execute:")
    code1 = """
for i in range(5):
    print(f"Processing step {i+1}/5...")
    import time
    time.sleep(0.2)
print("Basic example complete!")
"""
    print(code1)

    try:
        print("Executing with streaming=True...")
        result = await run_python(code1.strip(), stream=True)
        print(f"Final result: {result}")
    except Exception as e:
        print(f"Error (expected if Blender not running): {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 2: Non-streaming comparison
    print("Example 2: Non-streaming mode (for comparison)")
    code2 = "print('Hello from Blender!'); print('This is non-streaming mode')"
    print(f"Code: {code2}")

    try:
        print("Executing with streaming=False...")
        result = await run_python(code2, stream=False)
        print(f"Final result: {result}")
    except Exception as e:
        print(f"Error (expected if Blender not running): {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 3: Error handling in streaming
    print("Example 3: Error handling in streaming mode")
    code3 = """
print("Starting operation...")
print("This will work fine")
undefined_variable  # This will cause an error
print("This won't be reached")
"""
    print(code3)

    try:
        print("Executing with streaming=True (will demonstrate error handling)...")
        result = await run_python(code3.strip(), stream=True)
        print(f"Final result: {result}")
    except Exception as e:
        print(f"Error caught (expected): {e}")

    print("\n" + "=" * 50 + "\n")
    print("Demo complete!")
    print("\nTo see streaming in action:")
    print("1. Start Blender")
    print("2. Enable the BPY MCP extension")
    print("3. Ensure the server is listening on localhost:4777")
    print("4. Run this script again")


if __name__ == "__main__":
    asyncio.run(demo_streaming())
