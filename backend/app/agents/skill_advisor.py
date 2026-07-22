import json
import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


def _load_skills(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


class SkillAdvisor(BaseAgent):
    """技能顾问 Agent。

    根据用户画像、目标岗位与匹配结果给出综合建议。
    """

    name = "skill_advisor"

    def advise(
        self,
        profile: dict[str, Any],
        job: Any,
        match_result: dict[str, Any],
    ) -> str:
        """生成综合职业发展建议文本。"""
        system_prompt = self._load_prompt()
        user_prompt = (
            f"用户画像：{profile}\n"
            f"目标岗位：{job.title if job else ''}\n"
            f"岗位要求技能：{', '.join(_load_skills(getattr(job, 'required_skills', '[]')))}\n"
            f"匹配结果：{match_result}\n"
            f"请给出综合建议。"
        )

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
        )

        if result.get("simulated"):
            return self._rule_based_advise(profile, job, match_result)

        advice = result.get("advice") or result.get("content") or result.get("summary")
        if not advice:
            return self._rule_based_advise(profile, job, match_result)
        return str(advice).strip()

    def _rule_based_advise(
        self,
        profile: dict[str, Any],
        job: Any,
        match_result: dict[str, Any],
    ) -> str:
        """无 LLM 时的规则建议。"""
        job_title = job.title if job else "目标岗位"

        matched = match_result.get("matched_skills") or []
        missing = match_result.get("missing_skills") or []
        transferable = match_result.get("transferable_skills") or []
        score = match_result.get("match_score", 0.0)

        parts: list[str] = []
        parts.append(f"针对【{job_title}】岗位，当前匹配度约为 {score:.0%}。")

        # 简历优化
        if matched:
            parts.append(
                f"简历优化：优先突出你已掌握的 {', '.join(matched[:5])} 等核心技能，"
                f"并用项目经历量化成果。"
            )
        else:
            parts.append("简历优化：目前与岗位核心技能的直接重叠较少，建议在项目描述中突出可迁移经验。")

        # 技能补强
        if missing:
            priority = missing[:5]
            parts.append(
                f"技能补强：重点补齐 {', '.join(priority)}，按优先级逐步学习。"
            )
        else:
            parts.append("技能补强：核心技能已基本覆盖，可进一步拓展高级实践与源码阅读能力。")

        # 可迁移技能
        if transferable:
            examples = transferable[:5]
            parts.append(
                f"可迁移技能：{', '.join(examples)} 与岗位需求相近，可在简历中强调相似项目经验。"
            )

        # 求职策略
        parts.append(
            "求职策略：结合目标岗位 JD 调整简历关键词，优先投递匹配度高的岗位，"
            "并在面试中展示学习路径与项目闭环能力。"
        )

        return "\n".join(parts)

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        profile = context.get("profile") or {}
        job = context.get("job")
        match_result = context.get("match_result") or {}
        advice = self.advise(profile, job, match_result)
        return {"advice": advice}
