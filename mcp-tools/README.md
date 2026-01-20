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
├── search_server/      # Your custom web search tool
│   ├── server.py       # The MCP server
│   └── requirements.txt
├── scraper_server/     # (future) Web scraper tool
└── reranker_server/    # (future) Result reranker tool
```

## How to Run

1. Install dependencies:
   ```bash
   cd search_server
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python server.py
   ```

3. Configure LibreChat to connect to it (see librechat.yaml)

## Learning Path

1. Start with `search_server` - basic DuckDuckGo search
2. Add `scraper_server` - fetch and parse web pages
3. Add `reranker_server` - use embeddings to rank results
