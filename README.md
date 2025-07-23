# Blender Add-on MCP Server

A Model Context Protocol (MCP) server for managing Blender add-ons and automation.

## Development Setup

This project uses `uv` for dependency management and follows strict coding standards.

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
git clone <repository-url>
cd mcp_bpy
uv sync
```

### Development Commands

```bash
# Run the MCP server
uv run mcp dev

# Run tests
uv run pytest

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run pyright
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
uv run pre-commit install
```

## Project Structure

```
bpy_mcp/
├── bpy_mcp/           # Main package
│   ├── __init__.py
│   └── server.py      # FastMCP server implementation
├── tests/             # Test suite
├── .github/           # CI/CD workflows
└── pyproject.toml     # Project configuration
```

## Standards

- Line length: 120 characters
- Python version: 3.12+
- Linting: Ruff
- Type checking: Pyright
- Testing: pytest
- Package management: uv only

## License

TBD
