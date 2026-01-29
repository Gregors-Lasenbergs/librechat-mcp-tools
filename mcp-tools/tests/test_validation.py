"""
Tests for the validation module.

Run with: pytest tests/test_validation.py -v
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.validation import validate_url, validate_max_results


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_https_url(self):
        """Should accept valid HTTPS URLs."""
        is_valid, error = validate_url("https://example.com")
        assert is_valid is True
        assert error == ""

    def test_valid_http_url(self):
        """Should accept valid HTTP URLs."""
        is_valid, error = validate_url("http://example.com/path?query=1")
        assert is_valid is True
        assert error == ""

    def test_empty_url(self):
        """Should reject empty URLs."""
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_none_url(self):
        """Should reject None."""
        is_valid, error = validate_url(None)
        assert is_valid is False

    def test_missing_scheme(self):
        """Should reject URLs without scheme."""
        is_valid, error = validate_url("example.com")
        assert is_valid is False
        assert "scheme" in error.lower()

    def test_file_scheme_blocked(self):
        """Should block file:// URLs (security)."""
        is_valid, error = validate_url("file:///etc/passwd")
        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_localhost_blocked(self):
        """Should block localhost (SSRF protection)."""
        is_valid, error = validate_url("http://localhost/admin")
        assert is_valid is False
        assert "internal" in error.lower() or "private" in error.lower()

    def test_127_ip_blocked(self):
        """Should block 127.x.x.x IPs."""
        is_valid, error = validate_url("http://127.0.0.1:8080/secret")
        assert is_valid is False

    def test_private_ip_10_blocked(self):
        """Should block 10.x.x.x private IPs."""
        is_valid, error = validate_url("http://10.0.0.1/internal")
        assert is_valid is False

    def test_private_ip_192_blocked(self):
        """Should block 192.168.x.x private IPs."""
        is_valid, error = validate_url("http://192.168.1.1/router")
        assert is_valid is False

    def test_private_ip_172_blocked(self):
        """Should block 172.16-31.x.x private IPs."""
        is_valid, error = validate_url("http://172.16.0.1/internal")
        assert is_valid is False

    def test_url_with_port(self):
        """Should handle URLs with ports correctly."""
        is_valid, error = validate_url("https://example.com:8443/api")
        assert is_valid is True

    def test_whitespace_stripped(self):
        """Should strip whitespace from URLs."""
        is_valid, error = validate_url("  https://example.com  ")
        assert is_valid is True


class TestValidateMaxResults:
    """Tests for max_results validation."""

    def test_valid_value(self):
        """Should accept valid integer within bounds."""
        result = validate_max_results(5)
        assert result == 5

    def test_none_returns_default(self):
        """Should return default for None."""
        result = validate_max_results(None)
        assert result == 5  # default from config

    def test_string_number_converted(self):
        """Should convert string numbers."""
        result = validate_max_results("10")
        assert result == 10

    def test_invalid_string_returns_default(self):
        """Should return default for invalid strings."""
        result = validate_max_results("not a number")
        assert result == 5  # default

    def test_below_minimum_clamped(self):
        """Should clamp values below minimum."""
        result = validate_max_results(0)
        assert result == 1  # min from config

    def test_negative_clamped(self):
        """Should clamp negative values."""
        result = validate_max_results(-5)
        assert result == 1

    def test_above_maximum_clamped(self):
        """Should clamp values above maximum."""
        result = validate_max_results(100)
        assert result == 20  # max from config

    def test_custom_bounds(self):
        """Should respect custom min/max bounds."""
        result = validate_max_results(50, min_val=10, max_val=30)
        assert result == 30

    def test_custom_default(self):
        """Should use custom default."""
        result = validate_max_results(None, default=10)
        assert result == 10
