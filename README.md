# XHS-MCP

一个基于 Model Context Protocol (MCP) 的小红书内容获取服务器，为 AI 助手（如 Claude）提供访问小红书内容的能力。

##  特性

-  **一键部署** - 无需复杂配置，快速上手
-  **安全可靠** - 基于 xhshow 的官方签名机制
-  **现代工具链** - 使用 uv 包管理器，依赖管理简单
-  **MCP 标准** - 完全兼容 MCP 协议，与 Claude Desktop 无缝集成
-  **功能完整** - 支持笔记获取、搜索、用户信息等核心功能

##  快速开始

### 前置要求

- Python 3.10 或更高版本
- uv 包管理器（推荐）或 pip

### 安装

#### 方法一：使用 uv（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/xhs-mcp.git
cd xhs-mcp

# 安装依赖
uv sync

# 设置环境变量
export XHS_A1_COOKIE="your_a1_cookie_value_here"

# 测试运行
uv run python -m xhs_mcp
```

#### 方法二：使用 pip

```bash
# 安装
pip install xhs-mcp

# 设置环境变量
export XHS_A1_COOKIE="your_a1_cookie_value_here"

# 运行服务器
xhs-mcp
```

### 获取 A1 Cookie

1. 打开浏览器，访问 [小红书官网](https://www.xiaohongshu.com)
2. 登录你的账号
3. 打开开发者工具（按 F12）
4. 切换到 **Application** 或 **存储** 标签
5. 在左侧找到 **Cookies** → **www.xiaohongshu.com**
6. 找到名为 `a1` 的 Cookie，复制它的值

### Claude Desktop 集成

在 Claude Desktop 的配置文件中添加以下内容：

#### macOS
编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

#### Windows
编辑 `%APPDATA%\Claude\claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "xhs-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "xhs_mcp"],
      "cwd": "/path/to/xhs-mcp",
      "env": {
        "XHS_A1_COOKIE": "你的a1cookie值"
      }
    }
  }
}
```

或者如果你使用了全局安装：

```json
{
  "mcpServers": {
    "xhs-mcp": {
      "command": "xhs-mcp",
      "env": {
        "XHS_A1_COOKIE": "你的a1cookie值"
      }
    }
  }
}
```

## 🛠️ 功能介绍

### MCP Tools（工具）

#### 1. `get_user_notes` - 获取用户笔记
```python
# 获取用户的笔记列表
get_user_notes(
    user_id="用户ID",
    cursor="",        # 分页游标，可选
    num=30           # 获取数量，最大30
)
```

#### 2. `get_note_detail` - 获取笔记详情
```python
# 获取笔记的详细内容
get_note_detail(
    note_id="笔记ID",
    xsec_source="pc_user"  # 来源标识，可选
)
```

#### 3. `search_notes` - 搜索笔记
```python
# 搜索相关笔记
search_notes(
    keyword="搜索关键词",
    page=1,              # 页码
    page_size=20,        # 每页数量
    sort="general",      # 排序：general/time_descending/popularity_descending
    note_type="0"        # 类型：0全部/1视频/2图文
)
```

#### 4. `get_user_info` - 获取用户信息
```python
# 获取用户基本信息
get_user_info(user_id="用户ID")
```

### MCP Resources（资源）

- `config://api` - API 配置信息
- `user://{user_id}/profile` - 用户资料缓存

## 📝 使用示例

在 Claude 中，你可以这样使用：

```
# 搜索美食相关笔记
请帮我搜索小红书上关于"成都美食"的笔记

# 获取特定用户的笔记
请获取用户ID为 "xxx" 的最新笔记

# 获取笔记详情
请获取笔记ID为 "xxx" 的详细内容
```

## ⚙️ 配置选项

通过环境变量配置：

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `XHS_A1_COOKIE` | 小红书 a1 cookie 值 | ✅ | - |
| `XHS_API_HOST` | API 主机地址 | ❌ | `https://edith.xiaohongshu.com` |
| `XHS_TIMEOUT` | 请求超时时间（秒） | ❌ | `30` |
| `XHS_MAX_RETRIES` | 最大重试次数 | ❌ | `3` |

## 开发

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/yourusername/xhs-mcp.git
cd xhs-mcp

# 安装开发依赖
uv sync --dev

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，设置你的 A1 Cookie
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_client.py

# 带覆盖率的测试
uv run pytest --cov=xhs_mcp

# 详细输出
uv run pytest -v
```

### 代码检查

```bash
# 代码格式检查
uv run ruff check src/ tests/

# 自动修复
uv run ruff check src/ tests/ --fix

# 代码格式化
uv run ruff format src/ tests/
```

### 开发模式运行

```bash
# 使用 MCP 开发工具
uv run mcp dev src/xhs_mcp/server.py

# 直接运行服务器
uv run python -m xhs_mcp
```

##  注意事项

1. **Cookie 有效期**：a1 Cookie 有一定的有效期，过期后需要重新获取
2. **请求频率**：请合理控制请求频率，避免被限制访问
3. **仅读取功能**：本工具仅提供内容读取功能，不涉及任何写入操作
4. **隐私保护**：请勿分享你的 Cookie 值，注意账号安全

##  故障排除

### 常见问题

#### 1. "XHS_A1_COOKIE environment variable is not set"
确保已正确设置环境变量：
```bash
export XHS_A1_COOKIE="your_cookie_value"
```

#### 2. "Rate limit exceeded" 或 "请求频率限制"
稍等片刻后重试，或检查 Cookie 是否有效。

#### 3. "Failed to generate signature"
确保 xhshow 库版本正确，尝试重新安装依赖：
```bash
uv sync --reinstall
```

#### 4. Claude Desktop 无法连接服务器
- 检查配置文件路径和格式是否正确
- 确保环境变量已正确设置
- 重启 Claude Desktop

### 调试模式

设置环境变量启用详细日志：
```bash
export PYTHONPATH=$PYTHONPATH:src
export XHS_DEBUG=1
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---


## TODO

 1. ci/cd git提交规范
 2. 测试
 3. 提供例子