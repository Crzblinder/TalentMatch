"""联网搜索 Agent。

根据用户输入的求职相关问题，自动选择搜索意图、调用搜索工具、
并对结果进行 LLM 摘要，最终返回结构化的求职情报。
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.agents.search_tool import search_web, summarize_search_results
from app.llm.factory import LLMClientFactory

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """联网智能搜索 Agent。

    输入：用户求职相关问题/关键词
    输出：结构化搜索结果摘要
    """

    name = "search_agent"

    def search(
        self,
        query: str,
        intent: str = "general",
        location: str | None = None,
        top_n: int = 5,
        summarize: bool = True,
    ) -> dict[str, Any]:
        """执行联网搜索并返回结构化结果。

        Args:
            query: 用户查询
            intent: 搜索意图（general/salary/interview/company/fresh_graduate/skill_trend）
            location: 地域限定
            top_n: 返回结果数
            summarize: 是否使用 LLM 对结果摘要
        """
        search_result = search_web(
            query=query,
            top_n=top_n,
            intent=intent,
            location=location,
        )

        summary = ""
        if summarize:
            llm = None
            if self._has_real_llm():
                try:
                    llm = LLMClientFactory.create(self.settings)
                except Exception as exc:
                    logger.warning("Failed to create LLM for summary: %s", exc)
            summary = summarize_search_results(
                query=search_result.get("query", query),
                results=search_result.get("results", []),
                llm_client=llm,
            )

        return {
            "query": search_result.get("query", query),
            "original_query": query,
            "intent": intent,
            "source": search_result.get("source", "unknown"),
            "results": search_result.get("results", []),
            "summary": summary,
            "error": search_result.get("error"),
        }

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        query = context.get("query") or context.get("text") or ""
        intent = context.get("intent", "general")
        location = context.get("location")
        top_n = context.get("top_n", 5)
        summarize = context.get("summarize", True)
        return self.search(query, intent, location, top_n, summarize)
