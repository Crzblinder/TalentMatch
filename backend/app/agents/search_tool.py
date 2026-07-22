"""联网搜索工具封装。

提供统一的网络搜索接口，支持 Bocha、智谱、SearXNG、Tavily 和 DuckDuckGo。
国内环境优先使用 Bocha / 智谱 / SearXNG；未配置或失败时按优先级自动降级。
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_search_query(
    keywords: str,
    intent: str = "general",
    location: str | None = None,
) -> str:
    """根据搜索意图构建更精准的查询词。"""
    parts = [keywords]
    if intent == "salary":
        parts.append("薪资待遇 平均薪资")
    elif intent == "interview":
        parts.append("面试经验 面经")
    elif intent == "company":
        parts.append("公司评价 工作体验")
    elif intent == "fresh_graduate":
        parts.append("应届生 校招")
    elif intent == "skill_trend":
        parts.append("技术趋势 招聘需求")
    if location:
        parts.append(location)
    return " ".join(parts)


def search_web(
    query: str,
    top_n: int = 5,
    intent: str = "general",
    location: str | None = None,
) -> dict[str, Any]:
    """执行联网搜索并返回结构化结果。

    搜索源优先级：Bocha -> 智谱 -> SearXNG -> Tavily -> DuckDuckGo。
    任一源失败或返回空结果时自动降级到下一源。

    Args:
        query: 用户原始查询词
        top_n: 返回结果数量
        intent: 搜索意图，影响查询词增强策略
        location: 地域限定（可选）

    Returns:
        {
            "query": 实际搜索查询,
            "source": "bocha" | "zhipu" | "searxng" | "tavily" | "duckduckgo" | "none",
            "results": [
                {"title": "...", "url": "...", "snippet": "..."}
            ],
            "error": "..."  # 仅在全部失败时出现
        }
    """
    settings = get_settings()
    final_query = _build_search_query(query, intent, location)

    providers: list[tuple[str, Any, Any]] = [
        ("bocha", settings.bocha_api_key, _search_bocha),
        ("zhipu", settings.zhipu_api_key, _search_zhipu),
        ("searxng", settings.searxng_base_url, _search_searxng),
        ("tavily", settings.tavily_api_key, _search_tavily),
        ("duckduckgo", True, _search_duckduckgo),
    ]

    for source, configured, func in providers:
        if not configured or configured == "dummy":
            continue
        try:
            result = func(final_query, top_n)
            if result and result.get("results"):
                result.setdefault("query", final_query)
                return result
        except Exception as exc:
            logger.warning("%s search failed: %s", source, exc)

    logger.warning("All search providers failed for query: %s", final_query)
    return {
        "query": final_query,
        "source": "none",
        "results": [],
        "error": "all providers failed",
    }


def _search_bocha(query: str, top_n: int) -> dict[str, Any] | None:
    """使用博查（Bocha）Web Search API 搜索。"""
    settings = get_settings()
    api_key = settings.bocha_api_key
    if not api_key:
        return None

    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "count": top_n,
        "freshness": "noLimit",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    results = []
    web_pages = data.get("data", {}).get("webPages", {})
    for item in web_pages.get("value", [])[:top_n]:
        results.append({
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", "") or item.get("summary", ""),
        })

    return {"query": query, "source": "bocha", "results": results}


def _search_zhipu(query: str, top_n: int) -> dict[str, Any] | None:
    """使用智谱 OpenAI-compatible 搜索模型搜索。"""
    settings = get_settings()
    api_key = settings.zhipu_api_key
    if not api_key:
        return None

    base_url = settings.zhipu_base_url.rstrip("/")
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "glm-4-search",
        "messages": [{"role": "user", "content": query}],
        "tools": [{
            "type": "web_search",
            "web_search": {
                "enable": True,
                "search_query": query,
                "search_result": True,
            },
        }],
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    results = []
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})

    # 尝试从工具调用中解析搜索引用
    for tool_call in message.get("tool_calls", []):
        function = tool_call.get("function", {})
        if function.get("name") != "web_search":
            continue
        try:
            args = json.loads(function.get("arguments", "{}"))
        except json.JSONDecodeError:
            continue
        for item in args.get("search_results", [])[:top_n]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("content", ""),
            })

    # 若模型直接返回内容，作为兜底摘要
    if not results:
        content = message.get("content", "")
        if content:
            results.append({
                "title": f"智谱搜索：{query}",
                "url": "",
                "snippet": str(content).strip(),
            })

    return {"query": query, "source": "zhipu", "results": results[:top_n]}


def _search_searxng(query: str, top_n: int) -> dict[str, Any] | None:
    """使用本地 SearXNG JSON API 搜索。"""
    settings = get_settings()
    base_url = settings.searxng_base_url.rstrip("/")
    params = {"q": query, "format": "json"}
    url = f"{base_url}/search?{urlencode(params)}"

    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", [])[:top_n]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        })

    return {"query": query, "source": "searxng", "results": results}


def _search_tavily(query: str, top_n: int) -> dict[str, Any] | None:
    """使用 Tavily API 搜索。"""
    settings = get_settings()
    api_key = settings.tavily_api_key
    if not api_key or api_key == "dummy":
        return None

    url = "https://api.tavily.com/search"
    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": top_n,
        "include_answer": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = []
            for item in data.get("results", [])[:top_n]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                })
            return {"query": query, "source": "tavily", "results": results}
    except urllib.error.HTTPError as exc:
        logger.error("Tavily search failed: %s", exc)
        raise
    except Exception as exc:
        logger.error("Tavily search error: %s", exc)
        raise


def _search_duckduckgo(query: str, top_n: int) -> dict[str, Any] | None:
    """使用 DuckDuckGo 搜索（无需 API Key）。"""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.error("duckduckgo-search is not installed")
        return {
            "query": query,
            "source": "duckduckgo",
            "results": [],
            "error": "duckduckgo-search package not installed",
        }

    try:
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=top_n):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                })
            return {"query": query, "source": "duckduckgo", "results": results}
    except Exception as exc:
        logger.error("DuckDuckGo search failed: %s", exc)
        raise


def summarize_search_results(
    query: str,
    results: list[dict[str, str]],
    llm_client: Any | None = None,
) -> str:
    """使用 LLM 对搜索结果进行摘要。

    如果没有配置 LLM，则返回简单的拼接摘要。
    """
    if not results:
        return f"未找到与「{query}」相关的网络信息。"

    context = "\n\n".join(
        f"[{i+1}] {r.get('title', '')}\n{r.get('snippet', '')}"
        for i, r in enumerate(results[:5])
    )

    if llm_client is None:
        return (
            f"基于搜索结果，关于「{query}」的信息如下：\n\n{context}\n\n"
            "（未配置 LLM，仅展示原始搜索摘要）"
        )

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="你是一名信息摘要助手，请根据搜索结果用简洁中文总结关键信息。"),
            HumanMessage(content=f"查询：{query}\n\n搜索结果：\n{context}\n\n请总结关键发现："),
        ]
        response = llm_client.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)
        return str(content).strip()
    except Exception as exc:
        logger.error("LLM summary failed: %s", exc)
        return context
