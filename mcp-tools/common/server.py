"""
Shared MCP server utilities.

Provides common setup for SSE transport and Starlette apps.
"""

from typing import List

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.routing import Route, Mount

from .config import config
from .logging import get_logger

logger = get_logger(__name__)


def create_error_response(message: str) -> List[types.TextContent]:
    """
    Create a properly formatted MCP error response.

    Args:
        message: Error message to return

    Returns:
        List containing error TextContent
    """
    return [types.TextContent(type="text", text=f"Error: {message}")]


def create_starlette_app(
    mcp_server: Server,
    server_name: str,
    port: int,
) -> Starlette:
    """
    Create a Starlette app with SSE transport for an MCP server.

    Args:
        mcp_server: The MCP Server instance
        server_name: Name for logging and health endpoint
        port: Port number (for logging only)

    Returns:
        Configured Starlette application
    """
    # Create SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Response:
        """Handle SSE connections from clients."""
        client_host = request.client.host if request.client else "unknown"
        logger.info(f"New SSE connection from {client_host}")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await mcp_server.run(
                    streams[0], streams[1], mcp_server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
            raise
        return Response()

    async def health(request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "server": server_name,
            "debug": config.debug,
        })

    # Create Starlette app
    app = Starlette(
        debug=config.debug,
        routes=[
            Route("/health", health),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    logger.info(f"Created Starlette app for {server_name}")
    logger.info(f"  SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  Health endpoint: http://localhost:{port}/health")
    logger.info(f"  Debug mode: {config.debug}")

    return app


def run_server(app: Starlette, port: int, server_name: str) -> None:
    """
    Run the Starlette app with uvicorn.

    Args:
        app: The Starlette application
        port: Port to listen on
        server_name: Name for logging
    """
    import uvicorn

    print("=" * 60)
    print(f" {server_name}")
    print("=" * 60)
    print(f" Server: http://localhost:{port}")
    print(f" SSE:    http://localhost:{port}/sse")
    print(f" Health: http://localhost:{port}/health")
    print(f" Debug:  {config.debug}")
    print("")
    print(f" For LibreChat (Docker): http://host.docker.internal:{port}/sse")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=port)
