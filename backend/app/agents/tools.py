"""Agent 可调用的工具集合（function calling / skills / MCP 入口）。

本模块面向应届毕业生的求职场景，提供联网搜索、模糊解析、障碍识别等能力。
工具定义采用 LangChain 标准格式，可被支持 function calling 的 LLM 直接调用。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.agents.search_tool import search_web
from app.config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 工具函数实现
# ---------------------------------------------------------------------------
def search_jobs(
    query: str,
    intent: str = "general",
    location: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """联网搜索与求职相关的信息（公司、面经、薪资、校招等）。

    当开启国内平台抓取且意图为招聘相关时，会额外补充 Boss 直聘 / 智联招聘结果。

    Args:
        query: 用户原始查询词
        intent: 搜索意图，可选 general/salary/interview/company/fresh_graduate/skill_trend
        location: 地域限定，如 "上海"、"北京"
        top_n: 返回结果数量，默认 5
    """
    result = search_web(query=query, intent=intent, location=location, top_n=top_n)

    settings = get_settings()
    if settings.domestic_crawler_enabled and intent in {"general", "fresh_graduate"}:
        try:
            # 避免在已运行的事件循环中调用 asyncio.run
            asyncio.get_running_loop()
            logger.debug("事件循环已运行，跳过同步国内平台补充抓取")
        except RuntimeError:
            try:
                from app.crawler.scraper import scrape_domestic_jobs

                extra = asyncio.run(scrape_domestic_jobs(query, location))
                if extra:
                    result["domestic_jobs"] = extra
            except Exception as exc:
                logger.warning("国内平台补充抓取失败: %s", exc)

    return result


def fuzzy_parse_resume(resume_text: str, focus: str = "auto") -> dict[str, Any]:
    """对简历文本进行模糊识别解析，适用于经历边界不清、零经验应届生等场景。

    Args:
        resume_text: 原始简历文本
        focus: 解析重点，可选 auto/experience/skills/obstacles
    """
    from app.services.resume_service import ResumeService

    service = ResumeService()
    parsed = service.parse_resume_text(
        resume_text,
        fuzzy=True,
        prompt_variant="fresh_graduate",
    )

    if focus in ("obstacles", "auto"):
        from app.agents.obstacle_detector import ObstacleDetector

        detector = ObstacleDetector()
        obstacles = detector.detect_from_resume(parsed)
        parsed["obstacles"] = obstacles

    return {"source": "llm_fuzzy_parser", "focus": focus, "fuzzy": True, "parsed": parsed}


def fuzzy_parse_jd(jd_text: str, focus: str = "auto") -> dict[str, Any]:
    """对岗位描述进行模糊识别解析，识别应届生友好度、隐性门槛等。

    Args:
        jd_text: 原始岗位描述文本
        focus: 解析重点，可选 auto/requirements/barriers/fresh_graduate_friendly
    """
    from app.agents.jd_parser import JDParser

    parser = JDParser(prompt_variant="fresh_graduate")
    parsed = parser.parse_jd(jd_text)

    if focus in ("barriers", "auto"):
        from app.agents.obstacle_detector import ObstacleDetector

        detector = ObstacleDetector()
        obstacles = detector.detect_from_jd(parsed)
        parsed["obstacles"] = obstacles

    return {"source": "llm_fuzzy_parser", "focus": focus, "parsed": parsed}


def detect_job_search_obstacles(
    resume_data: dict[str, Any] | None = None,
    jd_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """识别应届毕业生在求职过程中可能遇到的困境与障碍。

    Args:
        resume_data: 已解析的简历结构化数据
        jd_data: 已解析的岗位结构化数据
    """
    from app.agents.obstacle_detector import ObstacleDetector

    detector = ObstacleDetector()
    return detector.detect(resume=resume_data or {}, jd=jd_data or {})


# ---------------------------------------------------------------------------
# LangChain Tool 定义（function calling 使用）
# ---------------------------------------------------------------------------
def get_langchain_tools() -> list[Any]:
    """返回 LangChain Tool 列表，供支持 function calling 的 LLM 绑定。"""
    try:
        from langchain_core.tools import StructuredTool
    except ImportError as exc:  # pragma: no cover
        logger.warning("langchain_core.tools 不可用，返回空工具列表: %s", exc)
        return []

    return [
        StructuredTool.from_function(
            name="search_jobs",
            func=search_jobs,
            description="联网搜索求职相关信息，如公司评价、面经、薪资、校招动态、技术趋势等。",
        ),
        StructuredTool.from_function(
            name="fuzzy_parse_resume",
            func=fuzzy_parse_resume,
            description="对简历进行模糊识别解析，识别边界不清的经历、零经验场景、求职困境等。",
        ),
        StructuredTool.from_function(
            name="fuzzy_parse_jd",
            func=fuzzy_parse_jd,
            description="对岗位描述进行模糊识别解析，识别应届生友好度、隐性门槛、技能别名等。",
        ),
        StructuredTool.from_function(
            name="detect_job_search_obstacles",
            func=detect_job_search_obstacles,
            description="识别应届毕业生的求职困境与障碍，如经验不足、学历门槛、技能缺口等。",
        ),
    ]


# ---------------------------------------------------------------------------
# OpenAI / 通用 function calling schema（JSON Schema 格式）
# ---------------------------------------------------------------------------
def get_function_schemas() -> list[dict[str, Any]]:
    """返回 OpenAI 风格的 function schema 列表。"""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_jobs",
                "description": (
                    "联网搜索求职相关信息，如公司评价、面经、薪资、"
                    "校招动态、技术趋势等。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "用户原始查询词"},
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
            },
        },
        {
            "type": "function",
            "function": {
                "name": "fuzzy_parse_resume",
                "description": (
                    "对简历进行模糊识别解析，识别边界不清的经历、"
                    "零经验场景、求职困境等。"
                ),
                "parameters": {
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
            },
        },
        {
            "type": "function",
            "function": {
                "name": "fuzzy_parse_jd",
                "description": (
                    "对岗位描述进行模糊识别解析，识别应届生友好度、"
                    "隐性门槛、技能别名等。"
                ),
                "parameters": {
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
            },
        },
        {
            "type": "function",
            "function": {
                "name": "detect_job_search_obstacles",
                "description": "识别应届毕业生的求职困境与障碍。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resume_data": {
                            "type": "object",
                            "description": "已解析的简历结构化数据",
                        },
                        "jd_data": {
                            "type": "object",
                            "description": "已解析的岗位结构化数据",
                        },
                    },
                    "required": [],
                },
            },
        },
    ]


# ---------------------------------------------------------------------------
# 工具执行分发
# ---------------------------------------------------------------------------
def execute_tool_call(name: str, arguments: str | dict[str, Any]) -> dict[str, Any]:
    """根据 LLM 返回的 function call 执行对应工具并返回结果。"""
    if isinstance(arguments, str):
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            args = {"query": arguments}
    else:
        args = arguments or {}

    tool_map = {
        "search_jobs": search_jobs,
        "fuzzy_parse_resume": fuzzy_parse_resume,
        "fuzzy_parse_jd": fuzzy_parse_jd,
        "detect_job_search_obstacles": detect_job_search_obstacles,
    }

    tool = tool_map.get(name)
    if tool is None:
        return {"error": f"未知工具: {name}", "available_tools": list(tool_map.keys())}

    try:
        return tool(**args)
    except Exception as exc:  # pragma: no cover
        logger.exception("工具执行失败: %s", name)
        return {"error": f"工具 {name} 执行失败: {exc}"}
