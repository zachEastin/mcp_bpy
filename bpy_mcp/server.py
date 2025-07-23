"""FastMCP server for Blender Add-on management."""

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("BPYMCP", version="0.1.0")


@mcp.tool()
def hello_blender() -> str:
    """A simple test tool that returns a greeting from the Blender MCP server."""
    return "Hello from BPYMCP! Ready to manage Blender add-ons."


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
