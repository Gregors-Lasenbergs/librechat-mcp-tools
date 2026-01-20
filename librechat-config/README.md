# LibreChat Configuration

These config files go into your LibreChat installation folder.

## Setup

1. Clone LibreChat:
   ```bash
   git clone https://github.com/danny-avila/LibreChat.git
   ```

2. Copy these files into the LibreChat folder:
   ```bash
   cp librechat.yaml docker-compose.override.yml /path/to/LibreChat/
   ```

3. Create your `.env` file from the example:
   ```bash
   cp .env.example .env
   # Add your API keys (OPENAI_API_KEY, etc.)
   ```

4. Start LibreChat:
   ```bash
   docker compose up -d
   ```

## Files

- `librechat.yaml` - Configures the MCP server connection
- `docker-compose.override.yml` - Mounts the config file into Docker
