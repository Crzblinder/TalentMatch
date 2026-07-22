"""TalentMatch MCP Server 测试。

验证 stdio MCP Server 能正确暴露 4 个工具、schema 与配置文件一致，并能正常调用。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

# 避免测试期间触发真实 LLM / 数据库 / 向量库初始化
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_mcp_server.db")
os.environ.setdefault("VECTOR_DB_PATH", "./test_mcp_server_chroma")

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.config import get_settings

# 确保 backend 目录在路径中，便于直接导入 mcp_server
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import mcp_server as mcp_server_module  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """每个用例前后清空 settings 缓存。"""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mcp_config() -> dict[str, Any]:
    """加载 mcp_config.json。"""
    config_path = BACKEND_DIR / "app" / "skills" / "mcp_config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def server_params() -> StdioServerParameters:
    """构造连接当前 Python 解释器运行的 mcp_server.py 的参数。"""
    return StdioServerParameters(
        command=sys.executable,
        args=[str(BACKEND_DIR / "mcp_server.py"), "--log-level", "ERROR"],
        env={
            **os.environ,
            "OPENAI_API_KEY": "",
            "DATABASE_URL": "sqlite:///./test_mcp_server.db",
            "VECTOR_DB_PATH": "./test_mcp_server_chroma",
        },
        cwd=str(BACKEND_DIR),
    )


# ---------------------------------------------------------------------------
# Server 对象与工具注册测试
# ---------------------------------------------------------------------------
def test_server_name_and_version() -> None:
    """Server 名称与版本应与 mcp_config.json 一致。"""
    assert mcp_server_module.mcp.name == "talentmatch-job-search-assistant"
    assert mcp_server_module.mcp.version == "1.0.0"


def test_tools_list_matches_config(mcp_config: dict[str, Any]) -> None:
    """本地工具列表应与 mcp_config.json 中的定义完全一致。"""
    config_tools = {tool["name"]: tool for tool in mcp_config["tools"]}
    server_tools = {tool.name: tool for tool in mcp_server_module.TOOLS}

    assert set(server_tools.keys()) == set(config_tools.keys())

    for name, config_tool in config_tools.items():
        server_tool = server_tools[name]
        assert server_tool.name == config_tool["name"]
        assert server_tool.description == config_tool["description"]
        assert server_tool.inputSchema == config_tool["parameters"]


def test_tool_schemas_have_required_fields() -> None:
    """每个工具 schema 都应包含基本字段。"""
    for tool in mcp_server_module.TOOLS:
        assert tool.name
        assert tool.description
        assert tool.inputSchema.get("type") == "object"
        assert "properties" in tool.inputSchema


# ---------------------------------------------------------------------------
# 工具 handler 单元测试（不依赖完整 stdio 会话）
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_call_tool_search_jobs(monkeypatch: Any) -> None:
    """调用 search_jobs 时，应实际触发 app.agents.tools.search_jobs。"""
    from app.agents import tools as agents_tools

    def fake_search_jobs(
        query: str,
        intent: str = "general",
        location: str | None = None,
        top_n: int = 5,
    ) -> dict[str, Any]:
        return {
            "query": query,
            "intent": intent,
            "location": location,
            "top_n": top_n,
            "source": "mock",
            "results": [{"title": "Mock Result", "url": "https://example.com", "snippet": "..."}],
        }

    monkeypatch.setattr(agents_tools, "search_jobs", fake_search_jobs)

    result = await mcp_server_module.call_tool(
        "search_jobs",
        {"query": "Python 后端", "intent": "general", "top_n": 3},
    )

    assert len(result) == 1
    assert result[0].type == "text"
    payload = json.loads(result[0].text)
    assert payload["source"] == "mock"
    assert payload["top_n"] == 3
    assert len(payload["results"]) == 1


@pytest.mark.anyio
async def test_call_tool_unknown_tool() -> None:
    """调用未注册工具时，应返回包含 error 字段的响应。"""
    result = await mcp_server_module.call_tool("unknown_tool", {})

    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert "error" in payload
    assert "unknown_tool" in payload["error"]


@pytest.mark.anyio
async def test_call_tool_fuzzy_parse_resume(monkeypatch: Any) -> None:
    """调用 fuzzy_parse_resume 时，返回应包含 fuzzy 标识字段。"""
    from app.services import resume_service

    def fake_parse_resume_text(
        self: Any,
        resume_text: str,
        fuzzy: bool = False,
        prompt_variant: str = "default",
    ) -> dict[str, Any]:
        return {"raw_text": resume_text, "fuzzy": fuzzy}

    monkeypatch.setattr(
        resume_service.ResumeService, "parse_resume_text", fake_parse_resume_text
    )

    result = await mcp_server_module.call_tool(
        "fuzzy_parse_resume",
        {"resume_text": "Python 开发应届生", "focus": "skills"},
    )

    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert payload["fuzzy"] is True
    assert payload["focus"] == "skills"
    assert "parsed" in payload


@pytest.mark.anyio
async def test_call_tool_fuzzy_parse_jd(monkeypatch: Any) -> None:
    """调用 fuzzy_parse_jd 时，应正常返回解析结构。"""
    from app.agents import jd_parser

    def fake_parse_jd(self: Any, jd_text: str) -> dict[str, Any]:
        return {"raw_text": jd_text, "title": "测试岗位"}

    monkeypatch.setattr(jd_parser.JDParser, "parse_jd", fake_parse_jd)

    result = await mcp_server_module.call_tool(
        "fuzzy_parse_jd",
        {"jd_text": "招聘 Python 后端工程师", "focus": "requirements"},
    )

    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert payload["focus"] == "requirements"
    assert "parsed" in payload


@pytest.mark.anyio
async def test_call_tool_error_handling(monkeypatch: Any) -> None:
    """工具执行异常时，应返回包含 error 字段的响应，不抛出异常。"""
    from app.agents import tools as agents_tools

    def failing_search_jobs(**kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("模拟搜索失败")

    monkeypatch.setattr(agents_tools, "search_jobs", failing_search_jobs)

    result = await mcp_server_module.call_tool("search_jobs", {"query": "test"})

    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert "error" in payload
    assert "模拟搜索失败" in payload["error"]


# ---------------------------------------------------------------------------
# 完整 stdio 会话集成测试
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_stdio_client_lists_tools(
    server_params: StdioServerParameters,
    mcp_config: dict[str, Any],
) -> None:
    """通过 stdio 启动 Server，验证工具列表与配置文件一致。"""
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await session.initialize()
            assert init_result.serverInfo.name == "talentmatch-job-search-assistant"
            assert init_result.serverInfo.version == "1.0.0"

            tools_result = await session.list_tools()
            tool_names = {tool.name for tool in tools_result.tools}
            config_names = {tool["name"] for tool in mcp_config["tools"]}
            assert tool_names == config_names

            for tool in tools_result.tools:
                config_tool = next(t for t in mcp_config["tools"] if t["name"] == tool.name)
                assert tool.description == config_tool["description"]
                assert tool.inputSchema == config_tool["parameters"]


@pytest.mark.anyio
async def test_call_tool_detect_obstacles() -> None:
    """直接调用 handler 执行 detect_job_search_obstacles，验证返回结构。"""
    result = await mcp_server_module.call_tool(
        "detect_job_search_obstacles",
        {
            "resume_data": {
                "skills": ["Python"],
                "work_experience": [],
                "project_experience": [],
            },
            "jd_data": {
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "fresh_graduate_friendly": True,
                "barriers_for_fresh_graduates": [],
            },
        },
    )
    assert len(result) == 1
    payload = json.loads(result[0].text)
    assert "obstacles" in payload
    assert isinstance(payload["obstacles"], list)
    assert "summary" in payload
