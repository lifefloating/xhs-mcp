"""Xiaohongshu API client implementation."""

import json
import time
from typing import Any, Dict, Optional

import httpx
from xhshow import Xhshow

from .config import Config


class XHSError(Exception):
    """Base exception for XHS client errors."""
    pass


class APIError(XHSError):
    """API call error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(APIError):
    """Rate limit exceeded error."""
    pass


class XHSClient:
    """Xiaohongshu API client."""

    def __init__(self, config: Config):
        """Initialize XHS client with configuration."""
        self.config = config
        self.xhshow = Xhshow()
        self.base_url = config.api_host
        self.session: Optional[httpx.AsyncClient] = None
        self._user_cache = {}

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            headers=self._get_base_headers(),
            timeout=httpx.Timeout(self.config.timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    def _get_base_headers(self) -> Dict[str, str]:
        """Get base request headers."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
        }

    async def _make_request(
        self,
        method: str,
        uri: str,
        params: Optional[Dict] = None,
        payload: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with signature."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with XHSClient(config)' or call __aenter__")

        # Generate signature
        try:
            if method == "GET":
                signature = self.xhshow.sign_xs_get(
                    uri=uri,
                    a1_value=self.config.a1_cookie,
                    params=params or {}
                )
            else:
                signature = self.xhshow.sign_xs_post(
                    uri=uri,
                    a1_value=self.config.a1_cookie,
                    payload=payload or {}
                )
        except Exception as e:
            raise APIError(f"Failed to generate signature: {str(e)}")

        # Build request headers
        headers = {
            **self.session.headers,
            "x-s": signature,
            "x-t": str(int(time.time() * 1000)),
            "cookie": f"a1={self.config.a1_cookie}",
        }

        # Make request
        try:
            if method == "GET":
                response = await self.session.get(
                    f"{self.base_url}{uri}",
                    params=params,
                    headers=headers
                )
            else:
                response = await self.session.post(
                    f"{self.base_url}{uri}",
                    json=payload,
                    headers=headers
                )

            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if data.get("code") != 0 and data.get("code") is not None:
                if "限制" in data.get("msg", "") or data.get("code") == -100:
                    raise RateLimitError(
                        data.get("msg", "Rate limit exceeded"),
                        status_code=data.get("code"),
                        response=data
                    )
                raise APIError(
                    data.get("msg", f"API error: {data.get('code')}"),
                    status_code=data.get("code"),
                    response=data
                )

            return data

        except httpx.HTTPStatusError as e:
            raise APIError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {str(e)}")

    async def get_user_posted(
        self,
        user_id: str,
        cursor: str = "",
        num: int = 30
    ) -> Dict[str, Any]:
        """Get user's posted notes."""
        params = {
            "num": str(min(num, 30)),  # Max 30 per request
            "cursor": cursor,
            "user_id": user_id,
            "image_formats": "jpg,webp,avif"
        }

        return await self._make_request(
            method="GET",
            uri="/api/sns/web/v1/user_posted",
            params=params
        )

    async def get_note_by_id(
        self,
        note_id: str,
        xsec_source: str = "pc_user"
    ) -> Dict[str, Any]:
        """Get note details by ID."""
        params = {
            "source_note_id": note_id,
            "image_formats": "jpg,webp,avif",
            "extra": '{"need_body_topic":"1"}',
            "xsec_source": xsec_source,
            "xsec_token": ""
        }

        return await self._make_request(
            method="GET",
            uri="/api/sns/web/v1/feed",
            params=params
        )

    async def get_search_notes(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "general",
        note_type: str = "0"
    ) -> Dict[str, Any]:
        """Search for notes."""
        payload = {
            "keyword": keyword,
            "page": page,
            "page_size": min(page_size, 50),  # Max 50 per request
            "search_id": str(int(time.time() * 1000)),
            "sort": sort,  # general, time_descending, popularity_descending
            "note_type": note_type,  # 0: all, 1: video, 2: image
            "image_formats": ["jpg", "webp", "avif"]
        }

        return await self._make_request(
            method="POST",
            uri="/api/sns/web/v1/search/notes",
            payload=payload
        )

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        # Check cache first
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        params = {
            "target_user_id": user_id
        }

        result = await self._make_request(
            method="GET",
            uri="/api/sns/web/v1/user/otherinfo",
            params=params
        )

        # Cache the result
        if result.get("success"):
            self._user_cache[user_id] = result

        return result

    async def get_cached_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get cached user profile or fetch if not cached."""
        if user_id not in self._user_cache:
            await self.get_user_info(user_id)
        return self._user_cache.get(user_id, {"error": "User not found"})