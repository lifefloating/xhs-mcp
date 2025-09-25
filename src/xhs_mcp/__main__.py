"""CLI entry point for XHS-MCP server."""

import asyncio
import sys
from typing import Optional

from mcp.server.stdio import stdio_server

from . import mcp
from .server import cleanup


async def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Run the MCP server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(read_stream, write_stream)
    except KeyboardInterrupt:
        print("Server interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Cleanup resources
        try:
            await cleanup()
        except Exception as e:
            print(f"Cleanup error: {e}", file=sys.stderr)


def cli_main() -> None:
    """CLI wrapper for main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()