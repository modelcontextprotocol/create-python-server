# MCP Create Server

[![PyPI](https://img.shields.io/pypi/v/create-mcp-server)](https://pypi.org/project/create-mcp-server/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Create [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server projects with no build configuration.

## Quick Overview

```sh
# Using uvx (recommended)
uvx create-mcp-server

# Or using pip
pip install create-mcp-server
create-mcp-server
```

You don't need to install or configure any dependencies manually. The tool will set up everything you need to create an MCP server.

## Creating a Server

**You'll need to have [UV](https://docs.astral.sh/uv/) >= 0.4.10 installed on your machine.**

To create a new server, run either of these commands:

### Using uvx (recommended)
```sh
uvx create-mcp-server
```

### Using pip
```sh
pip install create-mcp-server
create-mcp-server
```

It will walk you through creating a new MCP server project. When complete, you'll have a new directory with this structure:

```
my-server/
├── README.md
├── pyproject.toml
└── src/
    └── my_server/
        ├── __init__.py
        └── server.py
```

No configuration or complicated folder structures, only the files you need to run your server.

Once installation is done, you can start the server:

```sh
cd my-server
uv sync --dev --all-extras
uv run my-server
```

## Features

- Simple command-line interface for creating new projects
- Auto-configures Claude Desktop app integration when available
- Uses [uvx](https://docs.astral.sh/uv/guides/tools/) for fast, reliable package management and project creation
- Sets up basic MCP server structure
- Uses the [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) for the server project

## Philosophy

- **Zero Configuration:** No need to manually set up project structure or dependencies.
- **Best Practices:** Follows Python packaging standards and MCP server patterns.
- **Batteries Included:** Comes with everything needed to start building an MCP server.

## License

Create MCP Server is open source software [licensed as MIT](https://opensource.org/licenses/MIT).
