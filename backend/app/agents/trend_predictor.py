import logging
from collections import Counter
from typing import Any

from app.agents.base import BaseAgent
from app.models.job import parse_required_skills

logger = logging.getLogger(__name__)


class TrendPredictor(BaseAgent):
    """趋势预测 Agent。

    基于聚合的岗位数据分析市场趋势；LLM 不可用时返回统计摘要。
    """

    name = "trend_predictor"

    def predict(self, job_data: list[dict[str, Any]]) -> dict[str, Any]:
        """分析岗位数据并返回趋势结果。"""
        system_prompt = self._load_prompt()
        user_prompt = f"请分析以下聚合岗位数据并返回趋势 JSON：\n\n{job_data}"

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        if result.get("simulated"):
            return self._rule_based_predict(job_data)

        return self._normalize_predict_result(result, job_data)

    def _rule_based_predict(self, job_data: list[dict[str, Any]]) -> dict[str, Any]:
        """无 LLM 时的统计摘要。"""
        if not job_data:
            return {
                "summary": "暂无岗位数据，无法分析趋势。",
                "top_skills": [],
                "avg_salary_range": "0k-0k",
                "hot_job_titles": [],
                "key_metrics": {
                    "job_count": 0,
                    "avg_salary_min": 0,
                    "avg_salary_max": 0,
                },
            }

        # 技能频次统计
        skill_counter: Counter = Counter()
        title_counter: Counter = Counter()
        total_min = 0
        total_max = 0

        for job in job_data:
            title = job.get("title", "")
            if title:
                title_counter[title] += 1
            # 兼容结构化技能格式，仅提取技能名称参与统计
            skills = parse_required_skills(job.get("required_skills", []))
            for skill_info in skills:
                skill_counter[skill_info["name"]] += 1
            total_min += job.get("salary_min", 0) or 0
            total_max += job.get("salary_max", 0) or 0

        n = len(job_data)
        avg_min = int(total_min / n)
        avg_max = int(total_max / n)

        top_skills = [s for s, _ in skill_counter.most_common(10)]
        hot_titles = [t for t, _ in title_counter.most_common(5)]

        return {
            "summary": (
                f"共分析 {n} 条岗位数据。平均薪资 {avg_min}-{avg_max} 元/月，"
                f"热门技能包括 {', '.join(top_skills[:5])}。"
            ),
            "top_skills": top_skills,
            "avg_salary_range": f"{avg_min // 1000}k-{avg_max // 1000}k",
            "hot_job_titles": hot_titles,
            "key_metrics": {
                "job_count": n,
                "avg_salary_min": avg_min,
                "avg_salary_max": avg_max,
            },
        }

    def _normalize_predict_result(
        self,
        result: dict[str, Any],
        job_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """校验并补充 LLM 返回的趋势结果。"""
        fallback = self._rule_based_predict(job_data)

        summary = result.get("summary") or fallback["summary"]
        top_skills = result.get("top_skills") or fallback["top_skills"]
        hot_job_titles = result.get("hot_job_titles") or fallback["hot_job_titles"]
        avg_salary_range = result.get("avg_salary_range") or fallback["avg_salary_range"]
        key_metrics = result.get("key_metrics") or fallback["key_metrics"]

        if isinstance(top_skills, str):
            top_skills = [top_skills]
        if isinstance(hot_job_titles, str):
            hot_job_titles = [hot_job_titles]

        top_skills = [str(s) for s in top_skills]
        hot_job_titles = [str(t) for t in hot_job_titles]

        if not isinstance(key_metrics, dict):
            key_metrics = fallback["key_metrics"]

        return {
            "summary": summary,
            "top_skills": top_skills,
            "avg_salary_range": avg_salary_range,
            "hot_job_titles": hot_job_titles,
            "key_metrics": key_metrics,
        }

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        job_data = context.get("job_data") or []
        return self.predict(job_data)
