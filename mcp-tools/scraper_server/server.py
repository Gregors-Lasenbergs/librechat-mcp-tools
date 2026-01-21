"""
Web Scraper MCP Server
This tool fetches the full content from a URL and extracts readable text.
Use it to get detailed information from pages found via web search.
"""
from typing import Any
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import uvicorn
import httpx
from bs4 import BeautifulSoup


# Create the MCP server instance
app = Server("web-scraper")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Tell LibreChat what tools this server provides."""
    return [
        types.Tool(
            name="scrape_url",
            description="Fetch a webpage and extract its text content. Use this to get the full content of a URL found in search results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch and extract content from"
                    }
                },
                "required": ["url"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Handle tool calls from the LLM."""
    if name == "scrape_url":
        return await scrape_url(arguments)
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def scrape_url(arguments: dict[str, Any]) -> list[types.TextContent]:
    """Fetch the URL and extract its text content."""
    url = arguments.get("url", "")

    if not url:
        return [types.TextContent(type="text", text="Error: No URL provided")]

    print(f"[scraper] Fetching: {url}")

    try:
        # Fetch the webpage
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
            response.raise_for_status()
            html = response.text

        # Parse HTML and extract text
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements (removes JavaScript code)
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Clean up extra whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Limit length (context limit)
        if len(clean_text) > 10000:
            clean_text = clean_text[:10000] + "\n\n[Content truncated...]"

        print(f"[scraper] Extracted {len(clean_text)} characters from {url}")

        return [types.TextContent(type="text", text=f"## Content from {url}\n\n{clean_text}")]

    except Exception as e:
        print(f"[scraper] Error: {str(e)}")
        return [types.TextContent(type="text", text=f"Error fetching URL: {str(e)}")]

# Create the SSE transport
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request) -> Response:
    """Handle SSE connection from LibreChat."""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
    return Response()

async def health(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "server": "web-scraper"})

# Create the Starlette web app
starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/health", health),
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
    print("=" * 60)
    print("Web Scraper MCP Server")
    print("=" * 60)
    print("")
    print("Starting server at: http://localhost:8081")
    print("")
    print("Endpoints:")
    print("  - SSE:     http://localhost:8081/sse")
    print("  - Health:  http://localhost:8081/health")
    print("")
    print("Configure LibreChat to connect to: http://host.docker.internal:8081/sse")
    print("=" * 60)

    uvicorn.run(starlette_app, host="0.0.0.0", port=8081)