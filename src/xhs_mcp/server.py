"""MCP server implementation for Xiaohongshu content access."""

import json
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

try:
    # Try relative import first (for when running as module)
    from .client import XHSClient
    from .config import Config
except ImportError:
    # Fall back to absolute import (for direct execution)
    import sys
    import os

    # Add the parent directory to sys.path to make imports work
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    from xhs_mcp.client import XHSClient
    from xhs_mcp.config import Config


# Create MCP server
mcp = FastMCP("XHS-MCP", dependencies=["xhshow", "httpx"])

# Global client instance - will be initialized when first tool is called
_xhs_client: XHSClient | None = None
_config: Config | None = None


async def get_client() -> XHSClient:
    """Get or create XHS client instance."""
    global _xhs_client, _config

    if _xhs_client is None:
        if _config is None:
            _config = Config.from_env()
        _xhs_client = XHSClient(_config)
        await _xhs_client.__aenter__()

    return _xhs_client


@mcp.tool()
async def get_user_notes(user_id: str, cursor: str = "", num: int = 30) -> Dict[str, Any]:
    """
    获取指定用户发布的笔记列表

    Args:
        user_id: 用户ID
        cursor: 分页游标，用于获取下一页内容
        num: 获取数量，最大30

    Returns:
        包含笔记列表的字典，包含notes数组和分页信息
    """
    try:
        client = await get_client()
        result = await client.get_user_posted(user_id, cursor, min(num, 30))

        # Format response for better readability
        if result.get("success") and "data" in result:
            notes = result["data"].get("notes", [])
            return {
                "success": True,
                "notes_count": len(notes),
                "notes": notes,
                "cursor": result["data"].get("cursor", ""),
                "has_more": result["data"].get("has_more", False),
            }
        else:
            return {"success": False, "error": "Failed to fetch user notes", "raw_response": result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_note_detail(
    note_id: str,
    xsec_source: str = "pc_user",
    xsec_token: str | None = None,
    prefer_method: str = "GET",
) -> Dict[str, Any]:
    """
    获取笔记详细内容

    Args:
        note_id: 笔记ID
        xsec_source: 来源标识，默认为pc_user

    Returns:
        笔记详细信息，包含内容、图片、作者等
    """
    try:
        client = await get_client()
        # 如果提供了 xsec_token，优先按 prefer_method 请求
        pm = prefer_method if xsec_token else "GET"
        result = await client.get_note_by_id(
            note_id, xsec_source, xsec_token=xsec_token, prefer_method=pm
        )

        if result.get("success") and "data" in result:
            return {"success": True, "note": result["data"]}
        else:
            return {
                "success": False,
                "error": "Failed to fetch note detail",
                "raw_response": result,
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_notes(
    keyword: str, page: int = 1, page_size: int = 20, sort: str = "general", note_type: str = "0"
) -> Dict[str, Any]:
    """
    搜索小红书笔记

    Args:
        keyword: 搜索关键词
        page: 页码，从1开始
        page_size: 每页数量，最大50
        sort: 排序方式 - general(综合), time_descending(最新), popularity_descending(最热)
        note_type: 笔记类型 - "0"(全部), "1"(视频), "2"(图文)

    Returns:
        搜索结果，包含匹配的笔记列表
    """
    try:
        client = await get_client()
        result = await client.get_search_notes(keyword, page, min(page_size, 50), sort, note_type)

        if result.get("success") and "data" in result:
            notes = result["data"].get("items", [])
            return {
                "success": True,
                "keyword": keyword,
                "total_count": result["data"].get("total", 0),
                "notes_count": len(notes),
                "notes": notes,
                "page": page,
                "has_more": len(notes) == page_size,
            }
        elif result.get("success") is False:
            # Handle auth issues specifically
            if "无登录信息" in result.get("msg", ""):
                import os

                cookie = os.getenv("XHS_A1_COOKIE", "NOT_SET")
                return {
                    "success": False,
                    "error": f"Authentication failed. Cookie value: {cookie[:20]}..."
                    if cookie != "NOT_SET"
                    else "XHS_A1_COOKIE not set",
                    "raw_response": result,
                }
            return {
                "success": False,
                "error": result.get("msg", "Search failed"),
                "raw_response": result,
            }
        else:
            return {"success": False, "error": "Search failed", "raw_response": result}

    except ValueError as e:
        # Config initialization error
        return {"success": False, "error": f"Configuration error: {str(e)}"}
    except Exception as e:
        import os

        cookie = os.getenv("XHS_A1_COOKIE", "NOT_SET")
        return {
            "success": False,
            "error": str(e),
            "debug_info": {
                "cookie_status": "present" if cookie != "NOT_SET" else "missing",
                "cookie_prefix": cookie[:20] if cookie != "NOT_SET" else None,
            },
        }


@mcp.tool()
async def get_user_info(user_id: str) -> Dict[str, Any]:
    """
    获取用户基本信息

    Args:
        user_id: 用户ID

    Returns:
        用户信息，包含昵称、粉丝数、关注数等
    """
    try:
        client = await get_client()
        result = await client.get_user_info(user_id)

        if result.get("success") and "data" in result:
            return {"success": True, "user": result["data"]}
        else:
            return {"success": False, "error": "Failed to fetch user info", "raw_response": result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.resource("config://api")
def get_api_config() -> str:
    """提供 API 端点配置信息"""
    config_data = {
        "base_url": "https://edith.xiaohongshu.com",
        "endpoints": {
            "user_posted": "/api/sns/web/v1/user_posted",
            "note_detail": "/api/sns/web/v1/feed",
            "search": "/api/sns/web/v1/search/notes",
            "user_info": "/api/sns/web/v1/user/otherinfo",
        },
        "description": "小红书 Web API 端点配置",
    }
    return json.dumps(config_data, ensure_ascii=False, indent=2)


@mcp.resource("user://{user_id}/profile")
async def get_user_profile_resource(user_id: str) -> str:
    """获取缓存的用户资料"""
    try:
        client = await get_client()
        profile = await client.get_cached_user_profile(user_id)
        return json.dumps(profile, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


# Cleanup function for proper client shutdown
async def cleanup():
    """Cleanup resources."""
    global _xhs_client
    if _xhs_client:
        await _xhs_client.__aexit__(None, None, None)
        _xhs_client = None
