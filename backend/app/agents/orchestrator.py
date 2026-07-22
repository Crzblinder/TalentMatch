"""Agent orchestrator for the job skill-map and talent-matching workflow."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.orm import Session

from app.agents.workflow import (
    build_job_match_graph,
    run_job_match_stream,
)

logger = logging.getLogger(__name__)


class JobMatchOrchestrator:
    """岗位匹配工作流编排器。

    封装 LangGraph 图的构建、同步执行与 SSE 流式执行。
    """

    def __init__(self, session: Session):
        self.session = session
        self.graph = build_job_match_graph(session)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """同步执行完整工作流。"""
        config = {"configurable": {"session": self.session}}
        return self.graph.invoke(state, config=config)

    async def stream(self, state: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """流式执行工作流并产出节点事件。"""
        async for event in run_job_match_stream(self.session, state):
            yield event


def get_orchestrator(session: Session) -> JobMatchOrchestrator:
    """工厂函数：创建编排器实例。"""
    return JobMatchOrchestrator(session)
