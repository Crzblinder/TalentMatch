"""TalentMatch MCP Server。

基于官方 mcp Python SDK 的 stdio 服务，暴露 4 个核心工具：
- search_jobs
- fuzzy_parse_resume
- fuzzy_parse_jd
- detect_job_search_obstacles

工具定义与 backend/app/skills/mcp_config.json 保持一致，供外部 MCP Client
（Claude Desktop、Cursor 等）调用。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any

import anyio
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server 与工具定义
# ---------------------------------------------------------------------------
SERVER_NAME = "talentmatch-job-search-assistant"
SERVER_VERSION = "1.0.0"

mcp = Server(
    name=SERVER_NAME,
    version=SERVER_VERSION,
    instructions=(
        "TalentMatch 应届毕业生求职助手 MCP Server，"
        "提供联网搜索、简历/岗位模糊解析、求职障碍识别等能力。"
    ),
)

# 工具 schema 必须与 backend/app/skills/mcp_config.json 完全一致
TOOLS: list[types.Tool] = [
    types.Tool(
        name="search_jobs",
        description="联网搜索求职相关信息，如公司评价、面经、薪资、校招动态、技能趋势等",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "intent": {
                    "type": "string",
                    "enum": [
                        "general",
                        "salary",
                        "interview",
                        "company",
                        "fresh_graduate",
                        "skill_trend",
                    ],
                    "description": "搜索意图",
                },
                "location": {"type": "string", "description": "地域限定"},
                "top_n": {"type": "integer", "description": "返回结果数量"},
            },
            "required": ["query"],
        },
    ),
    types.Tool(
        name="fuzzy_parse_resume",
        description="对简历进行模糊识别解析，识别边界不清的经历、零经验场景、求职困境等",
        inputSchema={
            "type": "object",
            "properties": {
                "resume_text": {"type": "string", "description": "原始简历文本"},
                "focus": {
                    "type": "string",
                    "enum": ["auto", "experience", "skills", "obstacles"],
                    "description": "解析重点",
                },
            },
            "required": ["resume_text"],
        },
    ),
    types.Tool(
        name="fuzzy_parse_jd",
        description="对岗位描述进行模糊识别解析，识别应届生友好度、隐性门槛、技能别名等",
        inputSchema={
            "type": "object",
            "properties": {
                "jd_text": {"type": "string", "description": "原始岗位描述文本"},
                "focus": {
                    "type": "string",
                    "enum": ["auto", "requirements", "barriers", "fresh_graduate_friendly"],
                    "description": "解析重点",
                },
            },
            "required": ["jd_text"],
        },
    ),
    types.Tool(
        name="detect_job_search_obstacles",
        description="识别应届毕业生的求职困境与障碍",
        inputSchema={
            "type": "object",
            "properties": {
                "resume_data": {"type": "object", "description": "已解析的简历结构化数据"},
                "jd_data": {"type": "object", "description": "已解析的岗位结构化数据"},
            },
        },
    ),
]


# ---------------------------------------------------------------------------
# 工具实现
# ---------------------------------------------------------------------------
def _load_tool_functions() -> dict[str, Any]:
    """延迟导入业务工具函数，避免启动时触发大量依赖初始化。"""
    from app.agents.tools import (
        detect_job_search_obstacles,
        fuzzy_parse_jd,
        fuzzy_parse_resume,
        search_jobs,
    )

    return {
        "search_jobs": search_jobs,
        "fuzzy_parse_resume": fuzzy_parse_resume,
        "fuzzy_parse_jd": fuzzy_parse_jd,
        "detect_job_search_obstacles": detect_job_search_obstacles,
    }


async def _call_sync_tool(tool_func: Any, arguments: dict[str, Any]) -> dict[str, Any]:
    """在线程池中执行同步工具函数，避免阻塞事件循环。"""
    return await anyio.to_thread.run_sync(lambda: tool_func(**arguments))


@mcp.list_tools()
async def list_tools() -> list[types.Tool]:
    """返回 TalentMatch 暴露的 MCP 工具列表。"""
    return TOOLS


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """根据工具名分发调用，并统一处理异常。"""
    logger.info("MCP call_tool: %s", name)

    tool_map = _load_tool_functions()
    tool_func = tool_map.get(name)
    if tool_func is None:
        return _error_response(f"未知工具: {name}")

    try:
        result = await _call_sync_tool(tool_func, arguments)
    except Exception as exc:  # pragma: no cover
        logger.exception("工具执行失败: %s", name)
        return _error_response(f"工具 {name} 执行失败: {exc}")

    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _error_response(message: str) -> list[types.TextContent]:
    """构造统一的错误响应。"""
    return [
        types.TextContent(
            type="text",
            text=json.dumps({"error": message}, ensure_ascii=False, indent=2),
        )
    ]


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mcp_server.py",
        description="TalentMatch MCP Server（stdio 模式）。",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别（默认 INFO）",
    )
    return parser.parse_args()


async def main() -> None:
    """启动 stdio MCP Server。"""
    args = _parse_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
