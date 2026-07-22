import logging
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.graph.skill_graph import get_cached_graph, get_related_skills
from app.models import Job
from app.models.job import parse_required_skills

logger = logging.getLogger(__name__)


class TalentMatcher(BaseAgent):
    """人才匹配 Agent。

    将用户技能画像与目标岗位进行匹配，综合技能权重、熟练度、经验年限与学历计算匹配分数。
    """

    name = "talent_matcher"

    def match(
        self,
        profile: dict[str, Any] | list[str],
        job: Job,
        session: Session,
    ) -> dict[str, Any]:
        """计算人才与岗位的匹配结果。"""
        # 兼容旧接口：profile 也可能直接是技能列表
        if isinstance(profile, list):
            profile = {"skills": profile}

        # 延迟导入，避免与 services 包产生循环依赖
        from app.services.skill_service import SkillService

        # 归一化用户技能与岗位需求技能，未识别的名称保留原始值
        skill_service = SkillService(session)
        profile_skills = [
            skill_service.normalize_skill_name(name) or name
            for name in profile.get("skills") or []
        ]
        profile = {**profile, "skills": profile_skills}

        # 解析岗位技能（支持简单列表与结构化字典两种格式）
        job_skill_items = [
            {
                "name": skill_service.normalize_skill_name(item["name"]) or item["name"],
                "weight": item["weight"],
                "category": item["category"],
            }
            for item in parse_required_skills(job.required_skills)
        ]
        job_skills = [item["name"] for item in job_skill_items]

        system_prompt = self._load_prompt()
        user_prompt = (
            f"用户技能：{', '.join(profile_skills)}\n"
            f"目标岗位：{job.title}\n"
            f"岗位要求技能：{', '.join(job_skills)}\n"
            f"请返回匹配结果 JSON。"
        )

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )

        if result.get("simulated"):
            return self._rule_based_match(profile, job, job_skill_items, job_skills, session)

        return self._normalize_match_result(
            result, profile, job, job_skill_items, job_skills, session
        )

    def _rule_based_match(
        self,
        profile: dict[str, Any],
        job: Job,
        job_skill_items: list[dict[str, Any]],
        job_skills: list[str],
        session: Session,
    ) -> dict[str, Any]:
        """无 LLM 时的规则匹配（使用升级后的综合算法）。"""
        profile_skills = profile.get("skills") or []
        profile_set = set(profile_skills)
        required_set = set(job_skills)

        matched = list(profile_set & required_set)
        missing = list(required_set - profile_set)

        # 可迁移技能：通过 skill_graph 的 similarity 关系查找
        transferable = self._find_transferable_skills(
            profile_set, required_set, missing, session
        )

        skill_score = self._compute_score(matched, missing, job_skill_items)
        experience_match = self._compute_experience_match(
            profile.get("experience_years") or profile.get("experience_level", "不限"),
            job.experience_level,
        )
        education_match = self._compute_education_match(
            profile.get("education_level", "不限"),
            job.education_level,
        )
        match_score = skill_score * 0.6 + experience_match * 0.25 + education_match * 0.15
        match_score = max(0.0, min(1.0, match_score))

        return {
            "match_score": round(match_score, 3),
            "skill_score": round(skill_score, 3),
            "experience_match": round(experience_match, 3),
            "education_match": round(education_match, 3),
            "matched_skills": matched,
            "missing_skills": missing,
            "transferable_skills": transferable,
            "analysis_summary": (
                f"匹配度 {match_score:.1%}，掌握 {len(matched)} 项核心技能，"
                f"缺失 {len(missing)} 项，可迁移 {len(transferable)} 项。"
            ),
        }

    def _normalize_match_result(
        self,
        result: dict[str, Any],
        profile: dict[str, Any],
        job: Job,
        job_skill_items: list[dict[str, Any]],
        job_skills: list[str],
        session: Session,
    ) -> dict[str, Any]:
        """校验并补充 LLM 返回的匹配结果，并用升级算法计算最终分数。"""
        # 以下技能名称已在 match() 中完成归一化
        profile_skills = profile.get("skills") or []
        profile_set = set(profile_skills)
        required_set = set(job_skills)

        matched = result.get("matched_skills") or []
        missing = result.get("missing_skills") or []
        transferable = result.get("transferable_skills") or []

        matched = [str(x) for x in matched if x in required_set and x in profile_set]
        missing = [str(x) for x in missing if x in required_set and x not in profile_set]
        transferable = [str(x) for x in transferable]

        # 补充规则计算中遗漏的可迁移技能
        existing_transferable = {t.split("->")[0] for t in transferable if "->" in t}
        extra = self._find_transferable_skills(
            profile_set, required_set, missing, session
        )
        for item in extra:
            source = item.split("->")[0] if "->" in item else item
            if source not in existing_transferable:
                transferable.append(item)

        # 重新规整缺失与匹配
        all_matched_set = set(matched) | {t.split("->")[-1] for t in transferable if "->" in t}
        missing = [s for s in required_set if s not in all_matched_set]
        matched = [s for s in required_set if s in profile_set]

        skill_score = self._compute_score(matched, missing, job_skill_items)
        experience_match = self._compute_experience_match(
            profile.get("experience_years") or profile.get("experience_level", "不限"),
            job.experience_level,
        )
        education_match = self._compute_education_match(
            profile.get("education_level", "不限"),
            job.education_level,
        )
        match_score = skill_score * 0.6 + experience_match * 0.25 + education_match * 0.15
        match_score = max(0.0, min(1.0, match_score))

        summary = result.get("analysis_summary") or (
            f"匹配度 {match_score:.1%}，掌握 {len(matched)} 项核心技能，"
            f"缺失 {len(missing)} 项，可迁移 {len(transferable)} 项。"
        )

        return {
            "match_score": round(match_score, 3),
            "skill_score": round(skill_score, 3),
            "experience_match": round(experience_match, 3),
            "education_match": round(education_match, 3),
            "matched_skills": matched,
            "missing_skills": missing,
            "transferable_skills": transferable,
            "analysis_summary": summary,
        }

    def _find_transferable_skills(
        self,
        profile_set: set[str],
        required_set: set[str],
        missing: list[str],
        session: Session,
    ) -> list[str]:
        """基于相似关系寻找可迁移技能。"""
        transferable: list[str] = []
        try:
            graph = get_cached_graph(session, relation_types=["similarity"])
        except Exception as exc:
            logger.warning("Failed to build skill graph for transferable lookup: %s", exc)
            return transferable

        for miss_skill in missing:
            if miss_skill not in required_set:
                continue
            related = get_related_skills(
                graph,
                miss_skill,
                relation_type="similarity",
                min_weight=0.5,
                limit=10,
            )
            for rel in related:
                neighbor = rel["skill"]
                if neighbor in profile_set:
                    transferable.append(f"{neighbor}->{miss_skill}")
                    break
        return transferable

    def _compute_score(
        self,
        matched: list[str],
        missing: list[str],
        required_items: list[dict[str, Any]],
    ) -> float:
        """基于技能权重、缺失惩罚与软技能折扣计算技能匹配分数。"""
        if not required_items:
            return 1.0

        def _adjusted_weight(item: dict[str, Any]) -> float:
            """计算调整后权重，软技能贡献降低 30%。"""
            weight = float(item.get("weight", 1.0))
            if item.get("category") == "soft":
                weight *= 0.7
            return weight

        total_weight = sum(_adjusted_weight(item) for item in required_items)
        if total_weight == 0:
            return 1.0

        required_by_name = {item["name"]: item for item in required_items}
        matched_weight = sum(
            _adjusted_weight(required_by_name[name])
            for name in matched
            if name in required_by_name
        )
        missing_weight = sum(
            _adjusted_weight(required_by_name[name])
            for name in missing
            if name in required_by_name
        )

        # 技能分数 = 匹配技能权重 / 总权重
        skill_coverage = matched_weight / total_weight
        # 缺失惩罚 = 缺失技能权重 / 总权重 * 0.5
        penalty = (missing_weight / total_weight) * 0.5
        return max(0.0, skill_coverage - penalty)

    def _compute_experience_match(self, profile_experience: Any, job_experience: str) -> float:
        """根据经验年限计算匹配分数。"""
        # 岗位要求为不限时，直接视为满分
        if job_experience == "不限":
            return 1.0

        profile_years = self._parse_experience_value(profile_experience)
        job_years = self._parse_experience_value(job_experience)

        # 用户经验在要求区间及其 1.5 倍范围内为满分
        if profile_years >= job_years and profile_years <= job_years * 1.5:
            return 1.0
        # 资历过高轻微扣分
        if profile_years > job_years * 1.5:
            return 0.9
        # 经验不足按年扣分，每差 1 年扣 0.15
        return max(0.0, 1.0 - (job_years - profile_years) * 0.15)

    def _parse_experience_value(self, value: Any) -> float:
        """将经验字符串或年数值统一映射为年数。"""
        if isinstance(value, (int, float)):
            return float(value)
        mapping = {
            "应届": 0,
            "1-3年": 2,
            "3-5年": 4,
            "5-10年": 7.5,
            "10年以上": 12,
            "不限": 0,
        }
        return mapping.get(str(value), 0)

    def _compute_education_match(self, profile_education: str, job_education: str) -> float:
        """根据学历等级计算匹配分数。"""
        mapping = {"博士": 5, "硕士": 4, "本科": 3, "大专": 2, "不限": 1}
        profile_level = mapping.get(profile_education, 1)
        job_level = mapping.get(job_education, 1)
        # 用户学历不低于岗位要求即为满分
        if profile_level >= job_level:
            return 1.0
        # 每低一级扣 0.3
        return max(0.0, 1.0 - (job_level - profile_level) * 0.3)

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        profile = context.get("profile") or {}
        # 兼容旧调用方式：仅传入 profile_skills 列表
        if not profile and "profile_skills" in context:
            profile = {"skills": context.get("profile_skills") or []}
        job = context.get("job")
        session = context.get("session")
        if job is None or session is None:
            raise ValueError("TalentMatcher.run requires 'job' and 'session' in context")
        return self.match(profile, job, session)
