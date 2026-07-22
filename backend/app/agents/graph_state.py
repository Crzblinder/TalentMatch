"""LangGraph 工作流全局状态定义。

每个图节点接收 JobMatchState，返回 Partial[JobMatchState] 增量更新。
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class JobMatchState(TypedDict, total=False):
    """岗位技能图谱与人才匹配 LangGraph 工作流的全局状态。

    total=False 表示所有字段均为可选，允许节点仅填充所需字段。
    """

    # ---- 输入（由调用方初始化） ----
    input_text: str
    profile: dict[str, Any] | None
    target_job: Any | None
    job_data: list[dict[str, Any]] | None

    # ---- 各节点输出 ----
    parsed_jd: dict[str, Any] | None
    parsed_resume: dict[str, Any] | None
    match_result: dict[str, Any] | None
    trend_analysis: dict[str, Any] | None
    learning_path: list[dict[str, Any]] | None
    advice: str | None
    obstacles: dict[str, Any] | None
    search_results: list[dict[str, Any]] | None

    # ---- 控制开关 ----
    fuzzy: bool
    enable_search: bool

    # ---- 元数据 ----
    # 使用 Annotated + operator.add 支持多个并行节点同时追加事件与耗时
    messages: Annotated[list[dict[str, Any]], operator.add]
    stream_events: Annotated[list[dict[str, Any]], operator.add]
    response_time_ms: Annotated[int, operator.add]
