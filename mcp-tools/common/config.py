"""
Configuration management using environment variables.

All settings can be overridden via environment variables.
Example: export MCP_DEBUG=true
"""

import os
from dataclasses import dataclass, field
from typing import List

def _get_bool_env(key: str, default: bool) -> bool:
    """Parse boolean from environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes")

def _get_int_env(key: str, default: int) -> int:
    """Parse integer from environment variable."""
    try:
        return int(os.environ.get(key, default))
    except ValueError:
        return default

def _get_float_env(key: str, default: float) -> float:
    """Parse float from environment variable."""
    try:
        return float(os.environ.get(key, default))
    except ValueError:
        return default

@dataclass
class Config:
    """Application configuration with environment variable overrides."""

    # Debug mode - NEVER enable in production
    debug: bool = field(
        default_factory=lambda: _get_bool_env("MCP_DEBUG", False)
    )

    # HTTP request timeout in seconds
    request_timeout: float = field(
        default_factory=lambda: _get_float_env("MCP_REQUEST_TIMEOUT", 15.0)
    )

    # Maximum content length for scraped pages (characters)
    max_content_length: int = field(
        default_factory=lambda: _get_int_env("MCP_MAX_CONTENT_LENGTH", 15000)
    )

    # Search settings
    default_search_results: int = field(
        default_factory=lambda: _get_int_env("MCP_DEFAULT_SEARCH_RESULTS", 5)
    )
    max_search_results: int = field(
        default_factory=lambda: _get_int_env("MCP_MAX_SEARCH_RESULTS", 20)
    )
    min_search_results: int = 1

    # Rate limiting: minimum seconds between requests
    rate_limit_seconds: float = field(
        default_factory=lambda: _get_float_env("MCP_RATE_LIMIT_SECONDS", 1.0)
    )

    # Security: allowed URL schemes
    allowed_schemes: List[str] = field(
        default_factory=lambda: ["http", "https"]
    )

    # Security: blocked host patterns (private networks, localhost)
    blocked_hosts: List[str] = field(
        default_factory=lambda: [
            "localhost",
            "127.",
            "10.",
            "192.168.",
            "172.16.", "172.17.", "172.18.", "172.19.",
            "172.20.", "172.21.", "172.22.", "172.23.",
            "172.24.", "172.25.", "172.26.", "172.27.",
            "172.28.", "172.29.", "172.30.", "172.31.",
            "169.254.",  # Link-local
            "[::1]",     # IPv6 localhost
            "[fe80:",    # IPv6 link-local
        ]
    )

    # Allowed content types for scraping
    allowed_content_types: List[str] = field(
        default_factory=lambda: ["text/html", "application/xhtml+xml"]
    )
# Global config instance - import this in other modules
config = Config()