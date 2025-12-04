"""
Entry point for running the JDBC MCP server.

Usage:
    python -m jdbc_mcp_server
"""

import sys
import logging

# CRITICAL: Configure logging to stderr ONLY
# MCP protocol uses stdout for JSON-RPC messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the JDBC MCP server."""
    try:
        from jdbc_mcp_server.server import mcp

        logger.info("Starting JDBC MCP Server...")
        mcp.run()

    except ImportError as e:
        logger.error(f"Failed to import server module: {e}")
        logger.error("Make sure all dependencies are installed: pip install -e .")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error starting server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
