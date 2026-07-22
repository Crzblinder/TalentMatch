"""仪表盘统计服务占位模块。

后续阶段将基于新的 Skill、Company、Job 模型实现真正的 Dashboard 统计。
"""

from typing import Any


class DashboardService:
    def __init__(self, db):
        self.db = db

    def get_stats(self) -> dict[str, Any]:
        return {}

    def get_trend(self, days: int = 30) -> list[dict[str, Any]]:
        return []

    def get_enterprise_detail(self, enterprise_id: int) -> dict[str, Any] | None:
        return None

    def get_enterprise_events(
        self, enterprise_id: int, skip: int = 0, limit: int = 20
    ) -> list[dict[str, Any]]:
        return []
