"""Test the run_python tool."""

import anyio
import pytest

from bpy_mcp.server import run_python


def test_run_python_no_connection():
    """Test behavior when not connected to Blender."""

    async def _test():
        from mcp import McpError

        # This should fail since we don't have a connection
        with pytest.raises(McpError) as exc_info:
            await run_python("bpy.app.version_string")

        error = exc_info.value.error
        assert error.code == 4001
        assert "Not connected to Blender" in error.message

    anyio.run(_test)


def test_run_python_import():
    """Test that the run_python function can be imported."""
    assert run_python is not None
    assert callable(run_python)
