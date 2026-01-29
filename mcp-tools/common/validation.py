"""
Input validation utilities.
Security-critical: validates URLs and other user inputs.
"""
from typing import Any, Optional, Tuple
from urllib.parse import urlparse

from .config import config
from .logging import get_logger

logger = get_logger(__name__)

def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate a URL for safety before fetching.

    Checks:
    - URL is not empty
    - Scheme is allowed (http/https only)
    - Host is not a private/internal address

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, "")
        If invalid: (False, "reason")
    """
    if not url:
        return False, "URL is empty"

    if not isinstance(url, str):
        return False, "URL must be a string"

    # Strip whitespaces
    url = url.strip()

    # Parse the URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        logger.warning(f"Failed to parse URL '{url}': {e}")
        return False, f"Invalid URL format: {e}"

    # Check scheme
    if not parsed.scheme:
        return False, "URL must include a scheme (http:// or https://)"

    if parsed.scheme.lower() not in config.allowed_schemes:
        return False, f"URl scheme '{parsed.scheme}' is not allowed. Use http or https"

    # Check host exxists
    if not parsed.netloc:
        return False, "URL must include a host"

    # extract host (remove port if present)
    host = parsed.netloc.lower()
    if ":" in host and not host.startswith("["):
        host = host.split(":")[0]

    # Check against blocked hosts
    for blocked in config.blocked_hosts:
        if host == blocked or host.startswith(blocked):
            logger.warning(f"Blocked URL to private host: {url}")
            return False, "Access to internal/private addresses is not allowed"

    return True, ""


def validate_max_results(
    value: Any,
    default: Optional[int] = None,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
) -> int:
    """
    Validate and clamp max_results parameter.

    Args:
        value: The input value (may be int, str, or None)
        default: Default if value is None (uses config if not specified)
        min_val: Minimum allowed value (uses config if not specified)
        max_val: Maximum allowed value (uses config if not specified)

    Returns:
        Validated integer within bounds
    """
    # Use config defaults if not specified
    if default is None:
        default = config.default_search_results
    if min_val is None:
        min_val = config.min_search_results
    if max_val is None:
        max_val = config.max_search_results

    # Handle None
    if value is None:
        return default

    # Try to convert to int
    try:
        result = int(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid max_results value '{value}', using default {default}")
        return default

    # Clamp to bounds
    if result < min_val:
        logger.debug(f"max_results {result} below minimum, clamping to {min_val}")
        return min_val
    if result > max_val:
        logger.debug(f"max_results {result} above maximum, clamping to {max_val}")
        return max_val

    return result