import json
import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ResumeOptimizer(BaseAgent):
    """简历优化 Agent。

    根据目标岗位 JD 的要求，动态修改简历中的项目经历、实习经历、个人优势等内容，
    并支持配置这些字段的排放顺序。
    """

    name = "resume_optimizer"

    def optimize_resume(
        self,
        resume_data: dict[str, Any],
        jd_text: str,
        field_order: list[str] | None = None,
    ) -> dict[str, Any]:
        """根据 JD 优化简历内容。

        Args:
            resume_data: 原始简历数据，包含 project_experience、work_experience、self_evaluation 等字段
            jd_text: 目标岗位描述文本
            field_order: 字段排放顺序，可选值：['project', 'internship', 'advantage'] 的排列组合

        Returns:
            优化后的简历数据，包含 optimized_project_experience、optimized_work_experience、
            optimized_self_evaluation、field_order 等字段
        """
        system_prompt = self._load_prompt()

        default_order = ["project", "internship", "advantage"]
        actual_order = field_order or default_order

        user_prompt = self._build_user_prompt(resume_data, jd_text, actual_order)

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        if result.get("simulated"):
            return self._fallback_optimize(resume_data, actual_order)

        return self._normalize_result(result, resume_data, actual_order)

    def _build_user_prompt(
        self,
        resume_data: dict[str, Any],
        jd_text: str,
        field_order: list[str],
    ) -> str:
        """构建用户提示词。"""
        order_labels = {
            "project": "项目经历",
            "internship": "实习经历",
            "advantage": "个人优势",
        }

        return f"""请根据以下目标岗位描述，优化简历内容。

## 目标岗位描述
{jd_text}

## 原始简历数据
{json.dumps(resume_data, ensure_ascii=False, indent=2)}

## 字段排放顺序要求
按以下顺序排列简历中的核心模块：{', '.join([order_labels.get(o, o) for o in field_order])}

## 优化要求
1. **项目经历优化**：重点突出与目标岗位技能要求相关的项目经验，量化成果，使用专业术语
2. **实习经历优化**：如果有实习经历，突出与目标岗位相关的实习内容和取得的成绩
3. **个人优势优化**：提炼与目标岗位匹配的核心竞争力，用简洁有力的语言表达

请输出优化后的简历数据，格式为 JSON。"""

    def _normalize_result(
        self,
        result: dict[str, Any],
        original_data: dict[str, Any],
        field_order: list[str],
    ) -> dict[str, Any]:
        """规范化优化结果。"""
        normalized = {
            "original_project_experience": original_data.get("project_experience") or [],
            "original_work_experience": original_data.get("work_experience") or [],
            "original_self_evaluation": original_data.get("self_evaluation") or "",
            "optimized_project_experience": result.get("optimized_project_experience") or [],
            "optimized_work_experience": result.get("optimized_work_experience") or [],
            "optimized_self_evaluation": result.get("optimized_self_evaluation") or "",
            "field_order": field_order,
            "optimization_notes": result.get("optimization_notes") or "",
            "suggested_changes": result.get("suggested_changes") or [],
        }

        for key in ("optimized_project_experience", "optimized_work_experience"):
            if isinstance(normalized[key], str):
                try:
                    normalized[key] = json.loads(normalized[key])
                except json.JSONDecodeError:
                    normalized[key] = []
            if not isinstance(normalized[key], list):
                normalized[key] = []

        return normalized

    def _fallback_optimize(
        self,
        resume_data: dict[str, Any],
        field_order: list[str],
    ) -> dict[str, Any]:
        """无 LLM 时的降级优化策略。"""
        return {
            "original_project_experience": resume_data.get("project_experience") or [],
            "original_work_experience": resume_data.get("work_experience") or [],
            "original_self_evaluation": resume_data.get("self_evaluation") or "",
            "optimized_project_experience": resume_data.get("project_experience") or [],
            "optimized_work_experience": resume_data.get("work_experience") or [],
            "optimized_self_evaluation": resume_data.get("self_evaluation") or "",
            "field_order": field_order,
            "optimization_notes": "未配置 LLM，返回原始简历数据",
            "suggested_changes": [],
        }

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        resume_data = context.get("resume_data") or {}
        jd_text = context.get("jd_text") or ""
        field_order = context.get("field_order")
        return self.optimize_resume(resume_data, jd_text, field_order)
