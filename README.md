# MCP Create Server

[![PyPI](https://img.shields.io/pypi/v/create-mcp-server)](https://pypi.org/project/create-mcp-server/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Create MCP server projects with no build configuration.

## Quick Overview

```sh
# Using pip
pip install create-mcp-server
create-mcp-server

# Or using uvx (recommended)
uvx create-mcp-server
```

You don't need to install or configure any dependencies manually. The tool will set up everything you need to create an MCP server.

## Creating a Server

**You'll need to have uv >= 0.4.10 installed on your machine.**

To create a new server, run either of these commands:

### Using pip
```sh
pip install create-mcp-server
create-mcp-server
```

### Using uvx (recommended)
```sh
uvx create-mcp-server
```

It will walk you through creating a new MCP server project. When complete, you'll have a new directory with this structure:

```
my-server/
├── README.md
├── pyproject.toml
├── src/
│   └── my_server/
│       ├── __init__.py
│       └── server.py
└── tests/
    └── __init__.py
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
- Uses uv for fast, reliable package management
- Sets up basic MCP server structure
- Includes example endpoints

## Philosophy

- **Zero Configuration:** No need to manually set up project structure or dependencies.
- **Best Practices:** Follows Python packaging standards and MCP server patterns.
- **Batteries Included:** Comes with everything needed to start building an MCP server.

## License

Create MCP Server is open source software [licensed as MIT](https://opensource.org/licenses/MIT).
