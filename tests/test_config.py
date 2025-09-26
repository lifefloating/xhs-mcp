"""Tests for configuration module."""

import pytest

from xhs_mcp.config import Config


def test_config_from_env_success(monkeypatch):
    """Test successful config creation from environment variables."""
    monkeypatch.setenv("XHS_A1_COOKIE", "test_cookie_value")
    monkeypatch.setenv("XHS_API_HOST", "https://test.api.com")
    monkeypatch.setenv("XHS_TIMEOUT", "60")

    config = Config.from_env()

    assert config.a1_cookie == "test_cookie_value"
    assert config.api_host == "https://test.api.com"
    assert config.timeout == 60
    assert config.max_retries == 3  # default value


def test_config_from_env_missing_cookie(monkeypatch):
    """Test config creation fails without a1 cookie."""
    monkeypatch.delenv("XHS_A1_COOKIE", raising=False)

    with pytest.raises(ValueError, match="XHS_A1_COOKIE environment variable is not set"):
        Config.from_env()


def test_config_from_env_defaults(monkeypatch):
    """Test config creation with default values."""
    monkeypatch.setenv("XHS_A1_COOKIE", "test_cookie")
    # Clear other env vars to test defaults
    monkeypatch.delenv("XHS_API_HOST", raising=False)
    monkeypatch.delenv("XHS_TIMEOUT", raising=False)
    monkeypatch.delenv("XHS_MAX_RETRIES", raising=False)

    config = Config.from_env()

    assert config.a1_cookie == "test_cookie"
    assert config.api_host == "https://edith.xiaohongshu.com"
    assert config.timeout == 30
    assert config.max_retries == 3


def test_config_from_dict():
    """Test config creation from dictionary."""
    data = {
        "a1_cookie": "dict_cookie",
        "api_host": "https://dict.api.com",
        "timeout": 45,
        "max_retries": 5,
    }

    config = Config.from_dict(data)

    assert config.a1_cookie == "dict_cookie"
    assert config.api_host == "https://dict.api.com"
    assert config.timeout == 45
    assert config.max_retries == 5
