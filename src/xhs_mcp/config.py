"""Configuration management for XHS-MCP."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for XHS-MCP server."""

    a1_cookie: str
    api_host: str = "https://edith.xiaohongshu.com"
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        a1_cookie = os.getenv("XHS_A1_COOKIE", "")
        if not a1_cookie:
            raise ValueError(
                "XHS_A1_COOKIE environment variable is not set. "
                "Please set it with your Xiaohongshu a1 cookie value."
            )

        return cls(
            a1_cookie=a1_cookie,
            api_host=os.getenv("XHS_API_HOST", "https://edith.xiaohongshu.com"),
            timeout=int(os.getenv("XHS_TIMEOUT", "30")),
            max_retries=int(os.getenv("XHS_MAX_RETRIES", "3"))
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        return cls(**data)