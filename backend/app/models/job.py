import json
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


def parse_required_skills(value: Any) -> list[dict[str, Any]]:
    """解析岗位要求技能，支持简单字符串列表与结构化字典列表两种格式。

    简单格式：["Python", "React"]
    结构化格式：[{"name": "Python", "weight": 0.8, "category": "hard"}, ...]
    缺失字段将使用默认值：weight=1.0，category="hard"。
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(value, list):
        return []

    items: list[dict[str, Any]] = []
    for entry in value:
        if isinstance(entry, str):
            items.append({"name": entry, "weight": 1.0, "category": "hard"})
            continue
        if isinstance(entry, dict):
            name = entry.get("name")
            if not name:
                continue
            try:
                weight = float(entry.get("weight", 1.0))
            except (TypeError, ValueError):
                weight = 1.0
            category = entry.get("category", "hard")
            if category not in ("hard", "soft"):
                category = "hard"
            items.append({"name": str(name), "weight": weight, "category": category})
    return items


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    city = Column(String(64), nullable=False, index=True)
    salary_min = Column(Integer, nullable=False)
    salary_max = Column(Integer, nullable=False)
    experience_level = Column(String(64), nullable=False, index=True)
    education_level = Column(String(32), nullable=False)
    required_skills = Column(Text, nullable=False, default="[]")
    description = Column(Text, nullable=False)
    posted_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="jobs")

    # 一个岗位可以被多个画像收藏
    favorite_jobs = relationship(
        "FavoriteJob",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
