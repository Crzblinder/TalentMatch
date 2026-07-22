"""search_tool 国产化搜索源单元测试。"""

from __future__ import annotations

import os
from typing import Any

import pytest

os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_search_tool.db")
os.environ.setdefault("VECTOR_DB_PATH", "./test_search_tool_chroma")

from app.agents import search_tool
from app.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """每个用例前后清空 settings 缓存，避免环境变量串扰。"""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_search_web_prefers_bocha_when_configured(monkeypatch: Any) -> None:
    """配置了 BOCHA_API_KEY 时，search_web 应优先调用 _search_bocha。"""
    monkeypatch.setenv("BOCHA_API_KEY", "test-bocha-key")
    monkeypatch.setenv("ZHIPU_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    get_settings.cache_clear()

    called: dict[str, str | None] = {"source": None}

    def fake_bocha(query: str, top_n: int) -> dict[str, Any]:
        called["source"] = "bocha"
        return {
            "query": query,
            "source": "bocha",
            "results": [{"title": "Bocha Result", "url": "https://bocha.ai", "snippet": "..."}],
        }

    def fake_zhipu(query: str, top_n: int) -> dict[str, Any] | None:
        called["source"] = "zhipu"
        return None

    def fake_searxng(query: str, top_n: int) -> dict[str, Any] | None:
        return {"query": query, "source": "searxng", "results": []}

    def fake_tavily(query: str, top_n: int) -> dict[str, Any] | None:
        return None

    def fake_duckduckgo(query: str, top_n: int) -> dict[str, Any] | None:
        return {"query": query, "source": "duckduckgo", "results": []}

    monkeypatch.setattr(search_tool, "_search_bocha", fake_bocha)
    monkeypatch.setattr(search_tool, "_search_zhipu", fake_zhipu)
    monkeypatch.setattr(search_tool, "_search_searxng", fake_searxng)
    monkeypatch.setattr(search_tool, "_search_tavily", fake_tavily)
    monkeypatch.setattr(search_tool, "_search_duckduckgo", fake_duckduckgo)

    result = search_tool.search_web("测试", top_n=3)

    assert called["source"] == "bocha"
    assert result["source"] == "bocha"
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Bocha Result"


def test_search_bocha_parses_response(monkeypatch: Any) -> None:
    """_search_bocha 能正确解析博查返回的 Bing-like JSON。"""
    monkeypatch.setenv("BOCHA_API_KEY", "test-bocha-key")
    monkeypatch.setenv("ZHIPU_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    get_settings.cache_clear()

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {
                "code": 200,
                "data": {
                    "webPages": {
                        "value": [
                            {
                                "name": "Bocha Title",
                                "url": "https://example.com",
                                "snippet": "Bocha snippet",
                            },
                            {
                                "name": "Bocha Title 2",
                                "url": "https://example.com/2",
                                "summary": "Bocha summary fallback",
                            },
                        ]
                    }
                },
            }

    monkeypatch.setattr(search_tool.requests, "post", lambda *args, **kwargs: FakeResponse())

    result = search_tool._search_bocha("测试", top_n=5)
    assert result is not None
    assert result["source"] == "bocha"
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Bocha Title"
    assert result["results"][0]["url"] == "https://example.com"
    assert result["results"][0]["snippet"] == "Bocha snippet"
    assert result["results"][1]["snippet"] == "Bocha summary fallback"


def test_search_searxng_parses_json(monkeypatch: Any) -> None:
    """_search_searxng 能正确解析 SearXNG 返回的 JSON 格式。"""
    monkeypatch.setenv("BOCHA_API_KEY", "")
    monkeypatch.setenv("ZHIPU_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    get_settings.cache_clear()

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {
                "query": "Python 后端",
                "number_of_results": 2,
                "results": [
                    {"title": "Result 1", "url": "http://a", "content": "Snippet 1"},
                    {"title": "Result 2", "url": "http://b", "content": "Snippet 2"},
                ],
            }

    monkeypatch.setattr(search_tool.requests, "get", lambda *args, **kwargs: FakeResponse())

    result = search_tool._search_searxng("Python 后端", top_n=5)

    assert result is not None
    assert result["source"] == "searxng"
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Result 1"
    assert result["results"][0]["url"] == "http://a"
    assert result["results"][0]["snippet"] == "Snippet 1"


def test_search_web_returns_empty_when_all_providers_fail(monkeypatch: Any) -> None:
    """所有搜索源均失败时返回空列表并标记 source 为 none。"""
    monkeypatch.setenv("BOCHA_API_KEY", "")
    monkeypatch.setenv("ZHIPU_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    get_settings.cache_clear()

    def fail(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("provider failed")

    monkeypatch.setattr(search_tool, "_search_bocha", fail)
    monkeypatch.setattr(search_tool, "_search_zhipu", fail)
    monkeypatch.setattr(search_tool, "_search_searxng", fail)
    monkeypatch.setattr(search_tool, "_search_tavily", lambda q, n: None)
    monkeypatch.setattr(search_tool, "_search_duckduckgo", fail)

    result = search_tool.search_web("测试", top_n=3)

    assert result["source"] == "none"
    assert result["results"] == []
    assert "error" in result
