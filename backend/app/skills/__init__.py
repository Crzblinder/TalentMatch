"""TalentMatch Skills 配置包。

定义可被 LLM / MCP / Agent 调用的技能集合，聚焦应届毕业生求职场景。
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent
SKILLS_CONFIG_PATH = SKILLS_DIR / "skills.json"
MCP_CONFIG_PATH = SKILLS_DIR / "mcp_config.json"


def load_skills_config() -> dict[str, Any]:
    """加载 skills.json 技能配置。"""
    try:
        with SKILLS_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("skills.json 不存在: %s", SKILLS_CONFIG_PATH)
        return {"version": "1.0.0", "skills": []}
    except json.JSONDecodeError as exc:
        logger.warning("skills.json 解析失败: %s", exc)
        return {"version": "1.0.0", "skills": []}


def load_mcp_config() -> dict[str, Any]:
    """加载 mcp_config.json MCP 配置。"""
    try:
        with MCP_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("mcp_config.json 不存在: %s", MCP_CONFIG_PATH)
        return {"name": "talentmatch-job-search-assistant", "tools": []}
    except json.JSONDecodeError as exc:
        logger.warning("mcp_config.json 解析失败: %s", exc)
        return {"name": "talentmatch-job-search-assistant", "tools": []}
