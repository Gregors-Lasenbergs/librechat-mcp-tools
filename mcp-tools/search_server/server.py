"""
Custom MCP Web Search Server (SSE Transport)

This is a simple MCP server that provides web search functionality using DuckDuckGo.
No API key required - completely free!

How it works:
1. This server runs on your Mac and exposes an HTTP endpoint
2. LibreChat (in Docker) connects to it via SSE (Server-Sent Events)
3. When the LLM needs to search the web, it calls our "web_search" tool
4. We search DuckDuckGo and return the results
5. The LLM uses these results to answer the user's question

To run:
    pip install -r requirements.txt
    python server.py

Server will start at: http://localhost:8080/sse
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
import re


# Create the MCP server instance
app = Server("web-search")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """
    Tell LibreChat what tools this server provides.
    """
    return [
        types.Tool(
            name="web_search",
            description="Search the web using DuckDuckGo. Use this to find current information, news, facts, or any information not in your training data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Handle tool calls from the LLM.
    """
    if name == "web_search":
        return await do_web_search(arguments)
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def do_web_search(arguments: dict[str, Any]) -> list[types.TextContent]:
    """
    Perform web search using DuckDuckGo's HTML interface.
    """
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    
    if not query:
        return [types.TextContent(type="text", text="Error: No search query provided")]
    
    print(f"[web_search] Searching for: {query}")
    
    try:
        # Use DuckDuckGo HTML search
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data={"q": query},
                headers=headers,
                follow_redirects=True,
                timeout=10.0
            )
            response.raise_for_status()
            html = response.text
        
        # Parse results from HTML
        results = []
        
        # Find all result blocks
        result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)</a>'
        
        links = re.findall(result_pattern, html)
        snippets = re.findall(snippet_pattern, html)
        
        # Clean up snippets (remove HTML tags)
        clean_snippets = []
        for snippet in snippets:
            clean = re.sub(r'<[^>]+>', '', snippet)
            clean_snippets.append(clean.strip())
        
        for i, (href, title) in enumerate(links[:max_results]):
            snippet = clean_snippets[i] if i < len(clean_snippets) else "No description"
            results.append({
                "title": title.strip(),
                "href": href,
                "body": snippet
            })
        
        print(f"[web_search] Found {len(results)} results")
        
        if not results:
            return [types.TextContent(type="text", text=f"No results found for: {query}")]
        
        # Format results for the LLM
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"**Result {i}:**\n"
                f"Title: {result.get('title', 'No title')}\n"
                f"URL: {result.get('href', 'No URL')}\n"
                f"Snippet: {result.get('body', 'No description')}\n"
            )
        
        output = f"## Search Results for: {query}\n\n" + "\n---\n".join(formatted_results)
        
        return [types.TextContent(type="text", text=output)]
        
    except Exception as e:
        print(f"[web_search] Error: {str(e)}")
        return [types.TextContent(type="text", text=f"Search error: {str(e)}")]


# ============================================================================
# SSE Transport Setup
# ============================================================================

sse = SseServerTransport("/messages/")


async def handle_sse(request: Request) -> Response:
    """Handle SSE connections from LibreChat"""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
    return Response()


async def health(request: Request) -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "server": "web-search-mcp"})


# Create the Starlette app
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
    print("Web Search MCP Server")
    print("=" * 60)
    print("")
    print("Starting server at: http://localhost:8080")
    print("")
    print("Endpoints:")
    print("  - SSE:     http://localhost:8080/sse")
    print("  - Health:  http://localhost:8080/health")
    print("")
    print("Configure LibreChat to connect to: http://host.docker.internal:8080/sse")
    print("=" * 60)
    
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080)
