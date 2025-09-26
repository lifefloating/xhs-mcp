#!/usr/bin/env python3
"""Test authentication with XHS API."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from xhs_mcp.client import XHSClient
from xhs_mcp.config import Config


async def test_auth():
    """Test authentication with current configuration."""
    print("Testing XHS Authentication...")
    print("-" * 50)

    # Check environment variable
    cookie = os.getenv("XHS_A1_COOKIE", "")
    print(f"XHS_A1_COOKIE from env: {'Present' if cookie else 'Not set'}")
    if cookie:
        print(f"Cookie length: {len(cookie)}")
        print(f"Cookie value: {cookie}")  # Show full cookie for debugging

    # Try to create config
    try:
        config = Config.from_env()
        print("\n✓ Config created successfully")
        print(f"  - a1_cookie: {config.a1_cookie}")
        print(f"  - api_host: {config.api_host}")
    except ValueError as e:
        print(f"\n✗ Config creation failed: {e}")
        return

    # Test with debug logging
    print("\nTesting search API with debug info...")

    # Create client and patch _make_request to see actual headers
    client = XHSClient(config)

    # Override _make_request to debug
    original_make_request = client._make_request

    async def debug_make_request(method, uri, params=None, payload=None):
        print(f"\nDebug Request Info:")
        print(f"  Method: {method}")
        print(f"  URI: {uri}")
        print(f"  A1 Cookie: {client.config.a1_cookie}")

        return await original_make_request(method, uri, params, payload)

    client._make_request = debug_make_request

    async with client:
        try:
            result = await client.get_search_notes(
                keyword="测试",
                page=1,
                page_size=1
            )

            print(f"\nAPI Response:")
            print(f"  - Success: {result.get('success', 'N/A')}")
            print(f"  - Code: {result.get('code', 'N/A')}")
            print(f"  - Message: {result.get('msg', 'N/A')}")

            if result.get("success"):
                print(f"✓ API call successful!")
                print(f"  - Found {result.get('data', {}).get('total', 0)} results")
            else:
                print(f"✗ API call failed!")
                print(f"  - Full response: {result}")

        except Exception as e:
            print(f"\n✗ Exception occurred: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Set the cookie for testing if not already set
    if not os.getenv("XHS_A1_COOKIE"):
        # Use the cookie from the user's settings
        os.environ["XHS_A1_COOKIE"] = "199848ffe8cel617rq2dck2maggblgkodq172yagi30000605458"

    asyncio.run(test_auth())