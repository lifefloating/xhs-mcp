"""CLI entry point for XHS-MCP server."""

import sys

from .server import mcp


def cli_main() -> None:
    """CLI wrapper for main function."""
    try:
        # Run the FastMCP server with stdio transport
        mcp.run("stdio")
    except KeyboardInterrupt:
        print("\nShutdown complete", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
