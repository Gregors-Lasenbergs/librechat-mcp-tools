"""
Web Search MCP Server

Provides web search functionality using DuckDuckGo.
No API key required - completely free!

To run:
    pip install -r requirements.txt
    python server.py

Environment variables:
    MCP_DEBUG=true              Enable debug mode
    MCP_RATE_LIMIT_SECONDS=1.0  Minimum seconds between requests
    MCP_MAX_SEARCH_RESULTS=20   Maximum results allowed
"""

import sys
import time
from pathlib import Path
from typing import Any, List

# Add parent directory to path for common module
sys.path.insert(0, str(Path(__file__).parent.parent))

import mcp.types as types
from ddgs import DDGS
from mcp.server.lowlevel import Server

from common import (
    config,
    get_logger,
    validate_max_results,
    create_starlette_app,
    create_error_response,
    run_server,
)

logger = get_logger("search-server")

# Server configuration
SERVER_NAME = "Web Search MCP Server"
SERVER_PORT = 8080

# Rate limiting state
_last_request_time: float = 0.0


def _check_rate_limit() -> bool:
    """
    Check if we're within rate limits.
    
    Returns:
        True if request is allowed, False if rate limited
    """
    global _last_request_time
    now = time.time()
    
    if now - _last_request_time < config.rate_limit_seconds:
        return False
    
    _last_request_time = now
    return True


# Create the MCP server instance
mcp_server = Server("web-search")


@mcp_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """Tell clients what tools this server provides."""
    return [
        types.Tool(
            name="web_search",
            description=(
                "Search the web using DuckDuckGo. Returns general web pages. "
                "Use this for finding information, documentation, tutorials, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": f"Number of results (1-{config.max_search_results}, default: {config.default_search_results})",
                        "minimum": config.min_search_results,
                        "maximum": config.max_search_results,
                        "default": config.default_search_results,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="news_search",
            description=(
                "Search for recent news articles using DuckDuckGo News. "
                "Use this when the user asks for current events, recent news, or latest updates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The news topic to search for",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": f"Number of results (1-{config.max_search_results}, default: {config.default_search_results})",
                        "minimum": config.min_search_results,
                        "maximum": config.max_search_results,
                        "default": config.default_search_results,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls from the LLM."""
    if name == "web_search":
        return await do_web_search(arguments)
    elif name == "news_search":
        return await do_news_search(arguments)
    else:
        logger.warning(f"Unknown tool requested: {name}")
        return create_error_response(f"Unknown tool: {name}")


async def do_web_search(arguments: dict[str, Any]) -> List[types.TextContent]:
    """
    Perform web search using DuckDuckGo.
    
    Args:
        arguments: Tool arguments containing 'query' and optional 'max_results'
        
    Returns:
        List of TextContent with search results or error
    """
    # Validate query
    query = arguments.get("query", "")
    if not query or not isinstance(query, str):
        return create_error_response("No search query provided")
    
    query = query.strip()
    if not query:
        return create_error_response("Search query is empty")
    
    # Validate max_results
    max_results = validate_max_results(arguments.get("max_results"))
    
    # Check rate limit
    if not _check_rate_limit():
        logger.warning(f"Rate limited search request for: {query}")
        return create_error_response(
            f"Rate limited. Please wait {config.rate_limit_seconds} seconds between requests."
        )
    
    logger.info(f"Web search for: '{query}' (max_results={max_results})")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        logger.info(f"Found {len(results)} web results for: '{query}'")
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"No results found for: {query}"
            )]
        
        # Format results for the LLM
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"**Result {i}:**\n"
                f"Title: {result.get('title', 'No title')}\n"
                f"URL: {result.get('href', 'No URL')}\n"
                f"Snippet: {result.get('body', 'No description')}\n"
            )
        
        output = f"## Web Search Results for: {query}\n\n" + "\n---\n".join(formatted_results)
        
        return [types.TextContent(type="text", text=output)]
        
    except Exception as e:
        logger.error(f"Web search error for '{query}': {e}")
        return create_error_response(f"Search failed: {str(e)}")


async def do_news_search(arguments: dict[str, Any]) -> List[types.TextContent]:
    """
    Perform news search using DuckDuckGo News.
    
    Args:
        arguments: Tool arguments containing 'query' and optional 'max_results'
        
    Returns:
        List of TextContent with news results or error
    """
    # Validate query
    query = arguments.get("query", "")
    if not query or not isinstance(query, str):
        return create_error_response("No search query provided")
    
    query = query.strip()
    if not query:
        return create_error_response("Search query is empty")
    
    # Validate max_results
    max_results = validate_max_results(arguments.get("max_results"))
    
    # Check rate limit
    if not _check_rate_limit():
        logger.warning(f"Rate limited news request for: {query}")
        return create_error_response(
            f"Rate limited. Please wait {config.rate_limit_seconds} seconds between requests."
        )
    
    logger.info(f"News search for: '{query}' (max_results={max_results})")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
        
        logger.info(f"Found {len(results)} news results for: '{query}'")
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"No news found for: {query}"
            )]
        
        # Format results for the LLM
        formatted_results = []
        for i, result in enumerate(results, 1):
            date = result.get('date', 'Unknown date')
            source = result.get('source', 'Unknown source')
            formatted_results.append(
                f"**Article {i}:**\n"
                f"Title: {result.get('title', 'No title')}\n"
                f"Source: {source}\n"
                f"Date: {date}\n"
                f"URL: {result.get('url', 'No URL')}\n"
                f"Summary: {result.get('body', 'No summary')}\n"
            )
        
        output = f"## News Results for: {query}\n\n" + "\n---\n".join(formatted_results)
        
        return [types.TextContent(type="text", text=output)]
        
    except Exception as e:
        logger.error(f"News search error for '{query}': {e}")
        return create_error_response(f"News search failed: {str(e)}")


# Create and run the app
if __name__ == "__main__":
    app = create_starlette_app(mcp_server, SERVER_NAME, SERVER_PORT)
    run_server(app, SERVER_PORT, SERVER_NAME)
