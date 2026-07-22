import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.graph.skill_graph import get_cached_graph, get_learning_path, get_related_skills

logger = logging.getLogger(__name__)


def _load_skills(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


class LearningPlanner(BaseAgent):
    """学习路径规划 Agent。

    根据缺失技能、当前技能与技能图谱关系生成学习路径。
    """

    name = "learning_planner"

    def plan(
        self,
        missing_skills: list[str],
        current_skills: list[str],
        session: Session,
    ) -> list[dict[str, Any]]:
        """生成学习路径。"""
        # 延迟导入，避免与 services 包产生循环依赖
        from app.services.skill_service import SkillService

        # 对输入技能名称做归一化，未识别的名称保留原始值
        skill_service = SkillService(session)
        missing_skills = [
            skill_service.normalize_skill_name(name) or name
            for name in missing_skills
        ]
        current_skills = [
            skill_service.normalize_skill_name(name) or name
            for name in current_skills
        ]

        system_prompt = self._load_prompt()
        user_prompt = (
            f"当前技能：{', '.join(current_skills)}\n"
            f"缺失技能：{', '.join(missing_skills)}\n"
            f"请基于技能图谱依赖关系生成学习路径 JSON 数组。"
        )

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        if result.get("simulated"):
            return self._rule_based_plan(missing_skills, current_skills, session)

        return self._normalize_plan_result(result, missing_skills, current_skills, session)

    def _rule_based_plan(
        self,
        missing_skills: list[str],
        current_skills: list[str],
        session: Session,
    ) -> list[dict[str, Any]]:
        """无 LLM 时基于图谱依赖关系排序生成学习路径。"""
        if not missing_skills:
            return []

        try:
            graph = get_cached_graph(session)
        except Exception as exc:
            logger.warning("Failed to build skill graph for learning plan: %s", exc)
            return self._default_plan(missing_skills)

        current_set = set(current_skills)
        remaining = set(missing_skills)
        plan: list[dict[str, Any]] = []

        # 迭代选择：优先选择前置依赖已被满足（current_set 中）或已在 plan 中的技能
        while remaining:
            selectable: list[str] = []
            for skill in remaining:
                if skill not in graph:
                    selectable.append(skill)
                    continue
                # 查找依赖当前技能的边（source=skill, relation=dependency）
                deps = [
                    rel["skill"]
                    for rel in get_related_skills(
                        graph,
                        skill,
                        relation_type="dependency",
                        min_weight=0.0,
                        limit=50,
                    )
                ]
                if all(d in current_set or d not in remaining for d in deps):
                    selectable.append(skill)

            if not selectable:
                # 出现循环依赖时直接全部加入
                selectable = list(remaining)

            # 按与当前技能集合的连通性（路径长度）排序，近的优先
            selectable.sort(key=lambda s: self._avg_distance(graph, s, current_set))

            for skill in selectable:
                deps = []
                if skill in graph:
                    deps = [
                        rel["skill"]
                        for rel in get_related_skills(
                            graph,
                            skill,
                            relation_type="dependency",
                            min_weight=0.0,
                            limit=50,
                        )
                        if rel["skill"] in current_set
                    ]
                plan.append(self._build_plan_item(skill, deps))
                current_set.add(skill)
                remaining.discard(skill)

        return plan

    def _default_plan(self, missing_skills: list[str]) -> list[dict[str, Any]]:
        """无图谱时的默认学习路径。"""
        return [self._build_plan_item(skill, []) for skill in missing_skills]

    def _build_plan_item(self, skill: str, prerequisites: list[str]) -> dict[str, Any]:
        """构造单条学习路径项。"""
        # 简单按名称长度与是否含 "高级" 等关键词估算难度
        if any(kw in skill for kw in ("架构", "高级", "资深", "总监")):
            difficulty = "高级"
            weeks = 8
        elif any(kw in skill for kw in ("框架", "引擎", "平台", "系统")):
            difficulty = "进阶"
            weeks = 4
        else:
            difficulty = "入门"
            weeks = 2

        resource_types = ["官方文档", "在线课程", "项目实战"]
        return {
            "skill": skill,
            "difficulty": difficulty,
            "estimated_weeks": weeks,
            "resource_type": resource_types[len(skill) % len(resource_types)],
            "prerequisites": prerequisites,
        }

    def _avg_distance(
        self,
        graph: Any,
        skill: str,
        current_set: set[str],
    ) -> float:
        """计算技能到当前技能集合的平均最短距离，用于排序。"""
        if skill in current_set:
            return 0.0
        if skill not in graph:
            return float("inf")

        distances = []
        for start in current_set:
            if start not in graph:
                continue
            path_result = get_learning_path(graph, start, skill)
            if path_result.get("found"):
                distances.append(len(path_result.get("path", [])))

        if not distances:
            return float("inf")
        return sum(distances) / len(distances)

    def _normalize_plan_result(
        self,
        result: dict[str, Any],
        missing_skills: list[str],
        current_skills: list[str],
        session: Session,
    ) -> list[dict[str, Any]]:
        """校验并补充 LLM 返回的学习路径。"""
        plan = result if isinstance(result, list) else result.get("learning_path") or []
        if not isinstance(plan, list):
            return self._rule_based_plan(missing_skills, current_skills, session)

        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in plan:
            if not isinstance(item, dict):
                continue
            skill = str(item.get("skill", ""))
            if not skill or skill in seen:
                continue
            seen.add(skill)
            normalized.append({
                "skill": skill,
                "difficulty": item.get("difficulty") or "入门",
                "estimated_weeks": int(item.get("estimated_weeks", 2)),
                "resource_type": item.get("resource_type") or "官方文档",
                "prerequisites": [str(p) for p in (item.get("prerequisites") or []) if p],
            })

        # 补充缺失但未出现的技能
        fallback = self._rule_based_plan(missing_skills, current_skills, session)
        normalized_skills = {item["skill"] for item in normalized}
        for item in fallback:
            if item["skill"] not in normalized_skills:
                normalized.append(item)

        # 如果 LLM 返回了完全不相关的技能，兜底使用规则路径
        if not normalized and missing_skills:
            normalized = fallback

        return normalized

    def run(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """BaseAgent 抽象方法实现。"""
        missing_skills = context.get("missing_skills") or []
        current_skills = context.get("current_skills") or []
        session = context.get("session")
        if session is None:
            raise ValueError("LearningPlanner.run requires 'session' in context")
        return self.plan(missing_skills, current_skills, session)
