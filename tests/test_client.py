"""Tests for XHS client module."""

from unittest.mock import MagicMock, patch
import pytest
import httpx

from xhs_mcp.client import XHSClient, APIError, RateLimitError
from xhs_mcp.config import Config


@pytest.fixture
def test_config():
    """Test configuration fixture."""
    return Config(
        a1_cookie="test_cookie", api_host="https://test.api.com", timeout=30, max_retries=3
    )


@pytest.fixture
def mock_xhshow():
    """Mock xhshow fixture."""
    with patch("xhs_mcp.client.Xhshow") as mock:
        mock_instance = mock.return_value
        mock_instance.sign_xs_get.return_value = "test_get_signature"
        mock_instance.sign_xs_post.return_value = "test_post_signature"
        yield mock_instance


@pytest.mark.asyncio
async def test_client_context_manager(test_config):
    """Test client as async context manager."""
    async with XHSClient(test_config) as client:
        assert client.session is not None
        assert isinstance(client.session, httpx.AsyncClient)

    # Session should be closed after exit
    assert client.session is None or client.session.is_closed


@pytest.mark.asyncio
async def test_get_user_posted_success(test_config, mock_xhshow):
    """Test successful user notes retrieval."""
    mock_response_data = {
        "code": 0,
        "success": True,
        "data": {
            "notes": [
                {"note_id": "123", "title": "Test Note"},
                {"note_id": "456", "title": "Another Note"},
            ],
            "cursor": "next_cursor",
            "has_more": True,
        },
    }

    async with XHSClient(test_config) as client:
        with patch.object(client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await client.get_user_posted("test_user", "cursor", 10)

            assert result == mock_response_data
            mock_get.assert_called_once()
            mock_xhshow.sign_xs_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_note_by_id_success(test_config, mock_xhshow):
    """Test successful note detail retrieval."""
    mock_response_data = {
        "code": 0,
        "success": True,
        "data": {"note_id": "123", "title": "Test Note", "desc": "Test description", "images": []},
    }

    async with XHSClient(test_config) as client:
        with patch.object(client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = await client.get_note_by_id("123")

            assert result == mock_response_data
            mock_xhshow.sign_xs_get.assert_called_once()


@pytest.mark.asyncio
async def test_search_notes_success(test_config, mock_xhshow):
    """Test successful notes search."""
    mock_response_data = {
        "code": 0,
        "success": True,
        "data": {
            "items": [
                {"note_id": "123", "title": "Search Result 1"},
                {"note_id": "456", "title": "Search Result 2"},
            ],
            "total": 100,
        },
    }

    async with XHSClient(test_config) as client:
        with patch.object(client.session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = await client.get_search_notes("test keyword", 1, 20)

            assert result == mock_response_data
            mock_xhshow.sign_xs_post.assert_called_once()


@pytest.mark.asyncio
async def test_api_error_handling(test_config, mock_xhshow):
    """Test API error handling."""
    error_response = {"code": -1, "msg": "API Error", "success": False}

    async with XHSClient(test_config) as client:
        with patch.object(client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = error_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with pytest.raises(APIError, match="API Error"):
                await client.get_user_posted("test_user")


@pytest.mark.asyncio
async def test_rate_limit_error(test_config, mock_xhshow):
    """Test rate limit error handling."""
    rate_limit_response = {"code": -100, "msg": "请求频率限制", "success": False}

    async with XHSClient(test_config) as client:
        with patch.object(client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = rate_limit_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            with pytest.raises(RateLimitError):
                await client.get_user_posted("test_user")


@pytest.mark.asyncio
async def test_http_error_handling(test_config, mock_xhshow):
    """Test HTTP error handling."""
    async with XHSClient(test_config) as client:
        with patch.object(client.session, "get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404, text="Not Found"),
            )

            with pytest.raises(APIError, match="HTTP 404"):
                await client.get_user_posted("test_user")


@pytest.mark.asyncio
async def test_user_info_caching(test_config, mock_xhshow):
    """Test user info caching."""
    mock_response_data = {
        "code": 0,
        "success": True,
        "data": {"user_id": "123", "nickname": "Test User"},
    }

    async with XHSClient(test_config) as client:
        with patch.object(client.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # First call should fetch from API
            result1 = await client.get_user_info("123")
            assert result1 == mock_response_data

            # Second call should use cache
            result2 = await client.get_cached_user_profile("123")
            assert result2 == mock_response_data

            # Should only have called API once
            mock_get.assert_called_once()
