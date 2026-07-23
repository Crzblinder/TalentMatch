"""提示词加载器与版本管理回归测试。"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "")

from app.prompts.loader import PromptLoader


@pytest.fixture
def loader() -> PromptLoader:
    return PromptLoader()


def test_load_default_variant(loader: PromptLoader) -> None:
    """默认路径应能加载已存在的 zero_shot 提示词。"""
    content = loader.load("jd_parser", "zero_shot")
    assert "JD" in content or "岗位描述" in content
    assert content.strip()


def test_load_variant_alias_default(loader: PromptLoader) -> None:
    """default 别名应映射到 zero_shot。"""
    default = loader.load("resume_parser", "default")
    zero_shot = loader.load("resume_parser", "zero_shot")
    assert default == zero_shot


def test_load_versioned_prompt(loader: PromptLoader) -> None:
    """指定版本时应优先加载版本化目录下的提示词。"""
    v1 = loader.load("jd_parser", "zero_shot", version="v1")
    default = loader.load("jd_parser", "zero_shot")
    assert "v1" in v1
    assert v1 != default


def test_load_versioned_fallback_to_zero_shot(loader: PromptLoader) -> None:
    """版本目录下不存在指定变体时，应 fallback 到同版本的 zero_shot。"""
    # resume_parser/v1 只有 zero_shot.txt，请求不存在的 cot 应 fallback
    content = loader.load("resume_parser", "cot", version="v1")
    assert "v1" in content


def test_load_versioned_fallback_to_unversioned(loader: PromptLoader) -> None:
    """版本目录不存在时，应回退到未版本化的提示词。"""
    # trend_predictor 没有 v1 目录，应回退到默认 zero_shot
    content = loader.load("trend_predictor", "zero_shot", version="v99")
    assert content.strip()
    assert "v99" not in content


def test_load_missing_agent_raises(loader: PromptLoader) -> None:
    """完全不存在的 Agent 应抛出 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError):
        loader.load("non_existent_agent", "zero_shot")


def test_base_agent_uses_prompt_version_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """BaseAgent 应根据 settings.prompt_version 加载对应版本的提示词。"""
    from app.agents.jd_parser import JDParser
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "prompt_version", "v1")

    agent = JDParser()
    prompt = agent._load_prompt()
    assert "v1" in prompt
