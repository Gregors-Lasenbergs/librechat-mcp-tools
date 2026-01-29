# Custom MCP Tools for LibreChat

This project contains custom MCP (Model Context Protocol) servers that you can plug into LibreChat.

## What is MCP?

MCP is an open protocol by Anthropic that lets AI models use external tools. Think of it as a standard way for LLMs to:
- Search the web
- Read files
- Execute code
- Call APIs
- And more...

## Project Structure

```
mcp-tools/
├── common/                 # Shared utilities
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logging.py         # Logging setup
│   ├── server.py          # Shared MCP server utilities
│   └── validation.py      # Input validation (security)
├── search_server/         # Web search tool (DuckDuckGo)
│   └── server.py
├── scraper_server/        # Web scraper tool
│   └── server.py
├── tests/                 # Unit tests
│   └── test_validation.py
├── requirements.txt       # Python dependencies
└── README.md
```

## Quick Start

1. **Install dependencies:**
   ```bash
   cd mcp-tools
   pip install -r requirements.txt
   ```

2. **Run the search server:**
   ```bash
   python search_server/server.py
   ```

3. **Run the scraper server (in another terminal):**
   ```bash
   python scraper_server/server.py
   ```

4. **Configure LibreChat** to connect to:
   - Search: `http://host.docker.internal:8080/sse`
   - Scraper: `http://host.docker.internal:8081/sse`

## Configuration

All settings can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_DEBUG` | `false` | Enable debug mode (verbose logging) |
| `MCP_REQUEST_TIMEOUT` | `15.0` | HTTP request timeout in seconds |
| `MCP_MAX_CONTENT_LENGTH` | `15000` | Max characters for scraped content |
| `MCP_DEFAULT_SEARCH_RESULTS` | `5` | Default number of search results |
| `MCP_MAX_SEARCH_RESULTS` | `20` | Maximum allowed search results |
| `MCP_RATE_LIMIT_SECONDS` | `1.0` | Minimum seconds between requests |

Example:
```bash
MCP_DEBUG=true MCP_MAX_SEARCH_RESULTS=10 python search_server/server.py
```

## Tools

### web_search

Search the web using DuckDuckGo. No API key required.

**Parameters:**
- `query` (required): The search query
- `max_results` (optional): Number of results (1-20, default: 5)

**Example:**
```json
{
  "query": "Python async programming",
  "max_results": 10
}
```

### scrape_url

Fetch a webpage and extract its text content.

**Parameters:**
- `url` (required): The URL to fetch (must be http or https)

**Example:**
```json
{
  "url": "https://example.com/article"
}
```

**Security features:**
- Blocks private/internal IP addresses (SSRF protection)
- Only allows http/https schemes
- Validates content-type is HTML

## Running Tests

```bash
cd mcp-tools
pytest tests/ -v
```

## Security Notes

- The scraper blocks access to private IP ranges (localhost, 10.x.x.x, 192.168.x.x, etc.)
- File:// URLs are blocked
- Only HTML content is parsed (PDFs, images, etc. are rejected)
- Rate limiting prevents abuse

## Development

### Adding a new tool

1. Create a new directory: `my_tool_server/`
2. Create `server.py` using the common module:
   ```python
   from common import (
       config,
       get_logger,
       create_starlette_app,
       create_error_response,
       run_server,
   )
   ```
3. Define your tools using the MCP SDK
4. Use `create_starlette_app()` and `run_server()` to start

### Logging

Use the shared logger:
```python
from common import get_logger

logger = get_logger("my-tool")
logger.info("Processing request")
logger.error("Something went wrong")
```

Set `MCP_DEBUG=true` for verbose debug logs.
