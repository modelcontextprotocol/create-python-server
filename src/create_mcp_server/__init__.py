import sys


def main():
    print(
        """\
This project is now deprecated.

Instead, create a single-file MCP server using the FastMCP API from the Python SDK (https://github.com/modelcontextprotocol/python-sdk), and use the `mcp` CLI tool to easily test, install, and run it.""",
        file=sys.stderr,
    )

    return 1
