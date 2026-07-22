"""应届毕业生求职困境与障碍识别 Agent。

结合简历解析结果与 JD 解析结果，识别应届毕业生在求职过程中可能面临的结构性障碍，
并提供可执行的应对建议。
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ObstacleDetector(BaseAgent):
    """求职困境识别 Agent。

    输入：简历结构化数据、JD 结构化数据（可选）
    输出：困境列表 + 应对建议
    """

    name = "obstacle_detector"

    # 预定义常见应届生求职困境标签
    _OBSTACLE_CATEGORIES = {
        "experience_gap": {
            "label": "经验不足",
            "description": "岗位明确要求工作经验，但应届生缺乏正式工作经历",
            "suggestions": [
                "用课程设计、竞赛项目、开源贡献替代工作成果",
                "投递标注「应届/实习生/校招」的岗位",
                "优先选择有导师带教或培训体系的团队",
            ],
        },
        "skill_gap": {
            "label": "技能缺口",
            "description": "岗位要求的核心技能与当前掌握的技能存在较大差距",
            "suggestions": [
                "制定 2-4 周突击学习计划，补齐岗位 TOP3 核心技能",
                "在简历项目描述中自然融入目标岗位关键词",
                "通过 GitHub/LeetCode 等技术社区补充实战证据",
            ],
        },
        "education_barrier": {
            "label": "学历门槛",
            "description": "JD 中隐含或明示 985/211/硕士优先等要求",
            "suggestions": [
                "用项目深度和实习经历弥补学校背景",
                "尝试内推、校友网络等绕过简历筛选",
                "关注中小型企业和快速发展的新兴团队",
            ],
        },
        "school_background": {
            "label": "院校背景",
            "description": "学校非目标院校，可能在简历初筛阶段处于劣势",
            "suggestions": [
                "突出专业排名、奖学金、竞赛成绩等个人亮点",
                "在自我评价中强调学习能力与自驱力",
                "用技术博客、开源作品建立个人品牌",
            ],
        },
        "major_mismatch": {
            "label": "专业不对口",
            "description": "所学专业与目标岗位关联度低",
            "suggestions": [
                "强调已自学的相关课程和项目经验",
                "补充在线课程证书（如 Coursera、极客时间等）",
                "选择对专业包容度较高的岗位或公司",
            ],
        },
        "fragmented_experience": {
            "label": "经历零散",
            "description": "实习或项目经历时间短、跳频高，缺乏连续性",
            "suggestions": [
                "将相关经历按主题整合，突出主线能力",
                "删除与目标岗位无关的短期经历",
                "用「能力标签」替代按时间罗列经历",
            ],
        },
        "career_gap": {
            "label": "空窗期",
            "description": "简历中存在较长时间没有学习/工作记录",
            "suggestions": [
                "说明空窗期间的学习、考证、兼职或作品集",
                "突出空窗期后技能的提升与项目产出",
                "避免在简历中过度强调空窗期本身",
            ],
        },
        "high_expectation": {
            "label": "期望过高",
            "description": "期望薪资或岗位级别明显超出应届生市场水平",
            "suggestions": [
                "参考行业应届生起薪，调整薪资期望",
                "优先选择有成长空间的公司而非只看薪资",
                "用「薪资面议」保留谈判空间",
            ],
        },
        "intense_competition": {
            "label": "竞争激烈",
            "description": "目标岗位投递人数多、录用率低",
            "suggestions": [
                "扩展投递渠道（校招、实习转正、内推）",
                "准备多个梯度岗位，避免 all-in 单一方向",
                "提前准备面试高频问题与项目细节",
            ],
        },
        "unknown_company": {
            "label": "公司信息不对称",
            "description": "对目标公司业务、面试流程、团队情况了解不足",
            "suggestions": [
                "使用联网搜索查询公司评价、面经、校招流程",
                "通过脉脉、牛客、知乎等社区收集真实信息",
                "面试前研究公司产品与技术栈",
            ],
        },
    }

    def detect(
        self,
        resume: dict[str, Any],
        jd: dict[str, Any],
    ) -> dict[str, Any]:
        """综合简历与 JD 识别求职困境。"""
        system_prompt = self._load_prompt()
        user_prompt = (
            f"简历数据：{resume}\n\n"
            f"岗位数据：{jd}\n\n"
            "请识别其中体现的应届毕业生求职困境，并返回结构化 JSON。"
        )

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        if result.get("simulated"):
            return self._rule_based_detect(resume, jd)

        return self._normalize_result(result, resume, jd)

    def detect_from_resume(self, resume: dict[str, Any]) -> dict[str, Any]:
        """仅根据简历识别困境。"""
        return self.detect(resume=resume, jd={})

    def detect_from_jd(self, jd: dict[str, Any]) -> dict[str, Any]:
        """仅根据 JD 识别困境（通常是岗位门槛）。"""
        return self.detect(resume={}, jd=jd)

    def _normalize_result(
        self,
        result: dict[str, Any],
        resume: dict[str, Any],
        jd: dict[str, Any],
    ) -> dict[str, Any]:
        """规范化 LLM 返回结果，并补充规则命中项。"""
        obstacles = result.get("obstacles") or []
        if not isinstance(obstacles, list):
            obstacles = []

        # 合并规则命中结果，去重
        rule_based = self._rule_based_detect(resume, jd)
        rule_obstacles = rule_based.get("obstacles", [])

        existing_keys = {self._key_of(o) for o in obstacles}
        for item in rule_obstacles:
            key = self._key_of(item)
            if key not in existing_keys:
                obstacles.append(item)
                existing_keys.add(key)

        summary = result.get("summary") or self._build_summary(obstacles)
        action_plan = result.get("action_plan") or self._build_action_plan(obstacles)

        return {
            "obstacles": obstacles,
            "summary": summary,
            "action_plan": action_plan,
            "severity_score": self._compute_severity_score(obstacles),
        }

    def _rule_based_detect(
        self,
        resume: dict[str, Any],
        jd: dict[str, Any],
    ) -> dict[str, Any]:
        """无 LLM 时的规则识别。"""
        obstacles: list[dict[str, Any]] = []

        # ---- 从简历提取 ----
        work = resume.get("work_experience") or []
        projects = resume.get("project_experience") or []
        education = resume.get("education") or []
        self_eval = resume.get("self_evaluation", "")
        job_intention = resume.get("job_intention") or {}

        if len(work) == 0 and len(projects) == 0:
            obstacles.append(self._make_obstacle("experience_gap", "缺少实习和项目经历"))

        # 检查是否有超过 3 个月的连续经历
        short_experiences = 0
        for item in work + projects:
            duration_months = self._estimate_months(
                item.get("start_date", ""), item.get("end_date", "至今")
            )
            if duration_months is not None and duration_months < 3:
                short_experiences += 1
        if short_experiences >= 2:
            obstacles.append(self._make_obstacle("fragmented_experience", "经历较零散"))

        # 专业不对口（仅在知道目标岗位时才有意义，这里做简单启发）
        major = ""
        if education:
            major = str(education[0].get("major", ""))
        target_position = job_intention.get("expected_position", "")
        if major and target_position and not self._major_matches_position(major, target_position):
            obstacles.append(self._make_obstacle("major_mismatch", f"专业 {major} 与目标岗位 {target_position} 关联度可能较低"))

        # 空窗期关键词
        if any(kw in self_eval for kw in ("二战", "空窗", "待业", "gap")):
            obstacles.append(self._make_obstacle("career_gap", "简历或自述中存在空窗期信号"))

        # ---- 从 JD 提取 ----
        jd_text = jd.get("raw_text", "")
        barriers = jd.get("barriers_for_fresh_graduates") or []
        fresh_friendly = jd.get("fresh_graduate_friendly", True)

        if not fresh_friendly:
            obstacles.append(self._make_obstacle("experience_gap", "该岗位对应届生友好度较低"))

        for barrier in barriers:
            barrier_lower = str(barrier).lower()
            if any(kw in barrier_lower for kw in ("经验", "年限", "年")):
                obstacles.append(self._make_obstacle("experience_gap", str(barrier)))
            elif any(kw in barrier_lower for kw in ("学历", "硕士", "博士", "985", "211")):
                obstacles.append(self._make_obstacle("education_barrier", str(barrier)))
            elif any(kw in barrier_lower for kw in ("独立负责", "核心", "上线项目")):
                obstacles.append(self._make_obstacle("skill_gap", str(barrier)))

        # JD 文本中的学历歧视
        if any(kw in jd_text for kw in ("985", "211", "双一流", "硕士优先")):
            obstacles.append(self._make_obstacle("education_barrier", "JD 中存在学历偏好表述"))

        # 技能缺口：粗略比较
        resume_skills = {s.lower() for s in resume.get("skills", [])}
        jd_skills = {s.lower() for s in jd.get("required_skills", [])}
        missing = jd_skills - resume_skills
        if missing and len(missing) >= 3:
            obstacles.append(
                self._make_obstacle(
                    "skill_gap",
                    f"核心技能缺口较多，如 {', '.join(list(missing)[:5])}",
                )
            )

        return {
            "obstacles": obstacles,
            "summary": self._build_summary(obstacles),
            "action_plan": self._build_action_plan(obstacles),
            "severity_score": self._compute_severity_score(obstacles),
        }

    def _make_obstacle(self, key: str, detail: str) -> dict[str, Any]:
        """根据困境 key 生成标准结构。"""
        meta = self._OBSTACLE_CATEGORIES.get(key, {
            "label": key,
            "description": "",
            "suggestions": [],
        })
        return {
            "key": key,
            "label": meta["label"],
            "detail": detail,
            "description": meta["description"],
            "suggestions": meta["suggestions"],
        }

    def _key_of(self, obstacle: dict[str, Any]) -> str:
        return f"{obstacle.get('key')}:{obstacle.get('detail', '')}"

    def _build_summary(self, obstacles: list[dict[str, Any]]) -> str:
        if not obstacles:
            return "当前未识别到明显求职困境，保持现有投递节奏即可。"
        labels = [o.get("label", "未命名") for o in obstacles]
        return f"识别到 {len(obstacles)} 项潜在困境：{', '.join(labels)}。建议按行动方案逐步优化。"

    def _build_action_plan(self, obstacles: list[dict[str, Any]]) -> list[str]:
        plans: list[str] = []
        for obstacle in obstacles:
            suggestions = obstacle.get("suggestions") or []
            if suggestions:
                plans.append(
                    f"【{obstacle.get('label', '')}】{obstacle.get('detail', '')}："
                    f"{suggestions[0]}"
                )
        if not plans:
            plans.append("持续优化简历，保持投递与复盘。")
        return plans

    def _compute_severity_score(self, obstacles: list[dict[str, Any]]) -> float:
        """简单严重度评分：0-1，困境越多越严重。"""
        if not obstacles:
            return 0.0
        # 每项按 0.12 累加，封顶 1.0
        return min(1.0, round(len(obstacles) * 0.12, 2))

    def _estimate_months(self, start: str, end: str) -> int | None:
        """粗略估算经历持续月数。"""
        import re
        from datetime import datetime

        m_start = re.search(r"(\d{4})[\.\-/](\d{1,2})", str(start))
        if not m_start:
            return None
        year_s, month_s = int(m_start.group(1)), int(m_start.group(2))

        if str(end) in ("至今", "现在", ""):
            now = datetime.now()
            year_e, month_e = now.year, now.month
        else:
            m_end = re.search(r"(\d{4})[\.\-/](\d{1,2})", str(end))
            if not m_end:
                return None
            year_e, month_e = int(m_end.group(1)), int(m_end.group(2))

        return max(0, (year_e - year_s) * 12 + (month_e - month_s))

    def _major_matches_position(self, major: str, position: str) -> bool:
        """粗略判断专业与岗位是否相关。"""
        major_lower = major.lower()
        position_lower = position.lower()
        mappings = {
            "计算机": ["前端", "后端", "算法", "开发", "工程师", "java", "python", "go"],
            "软件": ["前端", "后端", "算法", "开发", "工程师", "java", "python", "go"],
            "信息": ["产品", "运营", "数据", "分析", "开发", "工程师"],
            "电子": ["硬件", "嵌入式", "电子", "开发", "工程师"],
            "机械": ["机械", "结构", "仿真", "工程师"],
            "金融": ["金融", "投资", "分析师", "风控"],
        }
        for keyword, positions in mappings.items():
            if keyword in major_lower:
                return any(p in position_lower for p in positions)
        return True  # 未知专业默认不判定为不匹配

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        resume = context.get("resume") or {}
        jd = context.get("jd") or {}
        return self.detect(resume, jd)
