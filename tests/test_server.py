"""Test the basic MCP server functionality."""

from bpy_mcp.server import mcp


def test_server_creation():
    """Test that the MCP server can be created."""
    assert mcp is not None
    assert mcp.name == "BPYMCP"


def test_server_info():
    """Test server information."""
    # This is a basic test to ensure the server object has expected properties
    assert hasattr(mcp, "name")
    assert hasattr(mcp, "run")
