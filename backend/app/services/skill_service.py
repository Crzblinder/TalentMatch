"""技能相关服务。"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.graph.skill_graph import (
    get_cached_graph,
    get_related_skills,
    invalidate_graph_cache,
)
from app.models import Job, Skill, SkillRelation
from app.models.job import parse_required_skills
from app.services.cache_service import CACHE_KEYS, DEFAULT_TTLS, cached

logger = logging.getLogger(__name__)


def _parse_skills(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


class SkillService:
    def __init__(self, db: Session):
        self.db = db
        self._alias_cache: dict[str, str] | None = None

    # ------------------------------------------------------------------
    # 技能名称规范化
    # ------------------------------------------------------------------

    def build_alias_map(self) -> dict[str, str]:
        """构建别名到标准技能名称的映射表。

        遍历数据库中所有 Skill，将 skill.name 及其 aliases 中的每个别名
        都映射到 skill.name（小写后匹配）。
        """
        alias_map: dict[str, str] = {}
        for skill in self.db.query(Skill).all():
            alias_map[skill.name.lower()] = skill.name
            for alias in _parse_skills(skill.aliases):
                alias_key = alias.lower()
                if alias_key not in alias_map:
                    alias_map[alias_key] = skill.name
        return alias_map

    def _build_alias_cache(self) -> dict[str, str]:
        """构建并缓存 alias → 标准名称 的映射（大小写不敏感）。"""
        if self._alias_cache is not None:
            return self._alias_cache
        self._alias_cache = self.build_alias_map()
        return self._alias_cache

    def normalize_skill_name(self, name: str) -> str | None:
        """将单个技能名称归一化为数据库中的标准名称。

        匹配规则（大小写不敏感）：
        1. 优先匹配 Skill.name；
        2. 其次匹配 Skill.aliases 中的别名；
        3. 未匹配时返回 None。
        """
        if not name:
            return None
        cache = self._build_alias_cache()
        return cache.get(name.lower())

    def normalize_skill_names(
        self, skill_names: list[str]
    ) -> tuple[list[str], list[str]]:
        """批量归一化技能名称。

        返回 (normalized_names, unrecognized_names)：
        - normalized_names：成功映射到标准名称的技能列表（按首次出现顺序去重）；
        - unrecognized_names：未能识别的原始技能名称列表（按首次出现顺序去重）。
        """
        cache = self._build_alias_cache()
        normalized: list[str] = []
        unrecognized: list[str] = []
        seen_normalized: set[str] = set()
        seen_unrecognized: set[str] = set()

        for name in skill_names:
            if not name:
                continue
            standard = cache.get(name.lower())
            if standard is not None:
                if standard not in seen_normalized:
                    seen_normalized.add(standard)
                    normalized.append(standard)
            else:
                if name not in seen_unrecognized:
                    seen_unrecognized.add(name)
                    unrecognized.append(name)

        return normalized, unrecognized

    # ------------------------------------------------------------------
    # 技能 CRUD 与统计
    # ------------------------------------------------------------------

    def list_skills(self, category: str | None = None) -> dict[str, Any]:
        query = self.db.query(Skill)
        if category:
            query = query.filter(Skill.category == category)
        items = query.order_by(Skill.name).all()
        return {"total": len(items), "items": items}

    def get_skill(self, skill_id: int) -> Skill | None:
        return self.db.query(Skill).filter(Skill.id == skill_id).first()

    @cached(prefix=CACHE_KEYS["skill_graph"], ttl=DEFAULT_TTLS["skill_graph"])
    def get_related_skills(
        self,
        skill_name: str,
        relation_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        try:
            graph = get_cached_graph(self.db)
        except Exception as exc:
            logger.warning("Failed to build skill graph: %s", exc)
            return []
        return get_related_skills(
            graph, skill_name, relation_type=relation_type, limit=limit
        )

    def invalidate_cache(self) -> None:
        """使当前服务实例的别名缓存与全局技能图谱缓存失效。"""
        self._alias_cache = None
        invalidate_graph_cache()
        logger.info("Skill service cache invalidated")

    @cached(prefix=CACHE_KEYS["skill_statistics"], ttl=DEFAULT_TTLS["skill_statistics"])
    def get_skill_statistics(self) -> dict[str, Any]:
        total_skills = self.db.query(Skill).count()
        total_relations = self.db.query(SkillRelation).count()

        category_distribution = (
            self.db.query(Skill.category, func.count(Skill.id).label("count"))
            .group_by(Skill.category)
            .order_by(func.count(Skill.id).desc())
            .all()
        )

        # 技能热度：按在岗位需求中出现次数统计（兼容结构化技能格式）
        skill_counter: Counter = Counter()
        for row in self.db.query(Job.required_skills).all():
            for skill_info in parse_required_skills(row[0]):
                skill_counter[skill_info["name"]] += 1

        hot_skills = [
            {"skill": skill, "count": count}
            for skill, count in skill_counter.most_common(20)
        ]

        relation_type_distribution = (
            self.db.query(
                SkillRelation.relation_type, func.count(SkillRelation.id).label("count")
            )
            .group_by(SkillRelation.relation_type)
            .order_by(func.count(SkillRelation.id).desc())
            .all()
        )

        return {
            "total_skills": total_skills,
            "total_relations": total_relations,
            "category_distribution": [
                {"category": c, "count": n} for c, n in category_distribution
            ],
            "hot_skills": hot_skills,
            "relation_type_distribution": [
                {"relation_type": r, "count": n} for r, n in relation_type_distribution
            ],
        }
