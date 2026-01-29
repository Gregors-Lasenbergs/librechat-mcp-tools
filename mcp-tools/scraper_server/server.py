"""
Web Scraper MCP Server (Playwright Edition)

Fetches web pages using a headless browser and extracts readable text content.
Uses Playwright for JavaScript rendering - works with modern SPAs and dynamic sites.

To run:
    pip install -r requirements.txt
    playwright install chromium
    python server.py

Environment variables:
    MCP_DEBUG=true                  Enable debug mode
    MCP_REQUEST_TIMEOUT=30.0        Page load timeout (seconds)
    MCP_MAX_CONTENT_LENGTH=15000    Maximum characters to return
"""

import sys
import asyncio
from pathlib import Path
from typing import Any, List

# Add parent directory to path for common module
sys.path.insert(0, str(Path(__file__).parent.parent))

import mcp.types as types
from bs4 import BeautifulSoup
from mcp.server.lowlevel import Server
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from common import (
    config,
    get_logger,
    validate_url,
    create_starlette_app,
    create_error_response,
    run_server,
)

logger = get_logger("scraper-server")

# Server configuration
SERVER_NAME = "Web Scraper MCP Server"
SERVER_PORT = 8081

# Elements to remove (non-content elements)
REMOVE_ELEMENTS = [
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "canvas",
    "video",
    "audio",
    "form",
    "button",
    "input",
    "select",
    "textarea",
    "nav",
    "footer",
    "header",
    "aside",
]

# Create the MCP server instance
mcp_server = Server("web-scraper")


@mcp_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """Tell clients what tools this server provides."""
    return [
        types.Tool(
            name="scrape_url",
            description=(
                "Fetch a webpage using a headless browser and extract its text content. "
                "Works with JavaScript-rendered pages and modern websites. "
                "Use this to get the full content of a URL found in search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch (must be http or https)",
                    },
                    "wait_for_js": {
                        "type": "boolean",
                        "description": "Wait extra time for JavaScript to render (default: true)",
                        "default": True,
                    },
                },
                "required": ["url"],
            },
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls from the LLM."""
    if name == "scrape_url":
        return await scrape_url(arguments)
    else:
        logger.warning(f"Unknown tool requested: {name}")
        return create_error_response(f"Unknown tool: {name}")


async def scrape_url(arguments: dict[str, Any]) -> List[types.TextContent]:
    """
    Fetch a URL using Playwright and extract its text content.
    
    Args:
        arguments: Tool arguments containing 'url' and optional 'wait_for_js'
        
    Returns:
        List of TextContent with page content or error
    """
    url = arguments.get("url", "")
    wait_for_js = arguments.get("wait_for_js", True)
    
    # Validate URL (security check)
    is_valid, error_message = validate_url(url)
    if not is_valid:
        logger.warning(f"URL validation failed for '{url}': {error_message}")
        return create_error_response(error_message)
    
    url = url.strip()
    logger.info(f"Fetching URL with Playwright: {url}")
    
    try:
        async with async_playwright() as p:
            # Launch headless browser
            browser = await p.chromium.launch(headless=True)
            
            # Create a new page with a realistic viewport
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            
            # Navigate to the URL
            timeout_ms = int(config.request_timeout * 1000)
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            
            # Wait for JavaScript to render if requested
            if wait_for_js:
                await page.wait_for_timeout(1500)  # 1.5 seconds for JS rendering
            
            # Get the page content
            html = await page.content()
            
            # Get the title
            title = await page.title() or "No title"
            
            # Close the browser
            await browser.close()
        
        logger.info(f"Successfully loaded {url}")
        
        # Parse HTML and extract text
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove non-content elements
        for element in soup(REMOVE_ELEMENTS):
            element.decompose()
        
        # Try to find main content area
        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find(id="content") or
            soup.find(class_="content") or
            soup.find(role="main") or
            soup.find("body") or
            soup
        )
        
        # Get text content
        text = main_content.get_text(separator="\n", strip=True)
        
        # Clean up extra whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)
        
        # Truncate if too long
        if len(clean_text) > config.max_content_length:
            clean_text = clean_text[:config.max_content_length] + "\n\n[Content truncated...]"
        
        logger.info(f"Extracted {len(clean_text)} characters from {url}")
        
        return [types.TextContent(
            type="text",
            text=f"## {title}\n**URL:** {url}\n\n{clean_text}"
        )]
        
    except PlaywrightTimeout:
        logger.error(f"Timeout loading {url}")
        return create_error_response(f"Page load timed out after {config.request_timeout} seconds")
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return create_error_response(f"Failed to fetch URL: {str(e)}")


# Create and run the app
if __name__ == "__main__":
    app = create_starlette_app(mcp_server, SERVER_NAME, SERVER_PORT)
    run_server(app, SERVER_PORT, SERVER_NAME)
