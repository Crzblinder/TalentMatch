"""简历解析 Agent。"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.base import BaseAgent
from app.agents.jd_parser import _EDUCATION_PATTERNS, _EXPERIENCE_PATTERNS, _SKILL_KEYWORDS

logger = logging.getLogger(__name__)


class ResumeParser(BaseAgent):
    """中文简历解析 Agent。

    将原始简历文本解析为结构化字段；LLM 不可用时使用规则引擎解析。
    """

    name = "resume_parser"

    def parse_resume(self, resume_text: str) -> dict[str, Any]:
        """解析简历文本，返回结构化结果。"""
        system_prompt = self._load_prompt()
        user_prompt = f"请解析以下简历：\n\n{resume_text}"

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
        )

        # simulated 表示走了降级，基类未返回有效字段
        if result.get("simulated"):
            return self._rule_based_parse(resume_text)

        return self._normalize_parse_result(result, resume_text)

    def _normalize_parse_result(
        self, result: dict[str, Any], resume_text: str
    ) -> dict[str, Any]:
        """确保返回字段完整且类型正确。"""
        normalized: dict[str, Any] = {
            "basic_info": self._normalize_basic_info(result.get("basic_info") or {}),
            "education": self._normalize_experience_list(result.get("education") or []),
            "work_experience": self._normalize_experience_list(result.get("work_experience") or []),
            "project_experience": self._normalize_experience_list(result.get("project_experience") or []),
            "skills": result.get("skills") or [],
            "awards": result.get("awards") or [],
            "certifications": result.get("certifications") or [],
            "language_skills": result.get("language_skills") or [],
            "self_evaluation": result.get("self_evaluation", ""),
            "job_intention": self._normalize_job_intention(result.get("job_intention") or {}),
        }

        # 技能去重并过滤空值
        normalized["skills"] = self._dedup_and_clean(normalized["skills"])

        # 如果 LLM 没解析出技能，用规则补充
        if not normalized["skills"]:
            normalized["skills"] = self._extract_skills(resume_text)

        # 如果基本信息为空，用规则补充
        basic = normalized["basic_info"]
        if not basic.get("name"):
            basic["name"] = self._extract_name(resume_text)
        if not basic.get("phone"):
            basic["phone"] = self._extract_phone(resume_text)
        if not basic.get("email"):
            basic["email"] = self._extract_email(resume_text)
        if not basic.get("gender"):
            basic["gender"] = self._extract_gender(resume_text)
        if not basic.get("birth_date"):
            basic["birth_date"] = self._extract_birth_date(resume_text)
        if not basic.get("political_status"):
            basic["political_status"] = self._extract_political_status(resume_text)

        # 教育、工作、项目经历若为空，用规则补充
        if not normalized["education"]:
            normalized["education"] = self._extract_education(resume_text)
        if not normalized["work_experience"]:
            normalized["work_experience"] = self._extract_work_experience(resume_text)
        if not normalized["project_experience"]:
            normalized["project_experience"] = self._extract_project_experience(resume_text)

        # 求职意向若为空，用规则补充
        ji = normalized["job_intention"]
        if not ji.get("expected_position"):
            ji["expected_position"] = self._extract_expected_position(resume_text)

        return normalized

    # ------------------------------------------------------------------
    # 规则引擎兜底
    # ------------------------------------------------------------------
    def _rule_based_parse(self, resume_text: str) -> dict[str, Any]:
        """无 LLM 时的规则解析。"""
        return {
            "basic_info": {
                "name": self._extract_name(resume_text),
                "phone": self._extract_phone(resume_text),
                "email": self._extract_email(resume_text),
                "gender": self._extract_gender(resume_text),
                "birth_date": self._extract_birth_date(resume_text),
                "political_status": self._extract_political_status(resume_text),
                "marriage": "",
                "wechat": "",
                "qq": "",
                "id_card_type": "",
                "id_card_no": "",
                "hukou": "",
                "jiguan": "",
            },
            "education": self._extract_education(resume_text),
            "work_experience": self._extract_work_experience(resume_text),
            "project_experience": self._extract_project_experience(resume_text),
            "skills": self._extract_skills(resume_text),
            "awards": self._extract_awards(resume_text),
            "certifications": self._extract_certifications(resume_text),
            "language_skills": self._extract_language_skills(resume_text),
            "self_evaluation": self._extract_self_evaluation(resume_text),
            "job_intention": {
                "expected_position": self._extract_expected_position(resume_text),
                "expected_city": "",
                "expected_salary": "",
                "expected_industry": "",
            },
        }

    # ------------------------------------------------------------------
    # 字段归一化
    # ------------------------------------------------------------------
    def _normalize_basic_info(self, info: Any) -> dict[str, str]:
        defaults = {
            "name": "",
            "phone": "",
            "email": "",
            "gender": "",
            "birth_date": "",
            "political_status": "",
            "marriage": "",
            "wechat": "",
            "qq": "",
            "id_card_type": "",
            "id_card_no": "",
            "hukou": "",
            "jiguan": "",
        }
        if not isinstance(info, dict):
            return defaults
        for key in defaults:
            defaults[key] = str(info.get(key) or "").strip()
        return defaults

    def _normalize_job_intention(self, info: Any) -> dict[str, str]:
        defaults = {
            "expected_position": "",
            "expected_city": "",
            "expected_salary": "",
            "expected_industry": "",
        }
        if not isinstance(info, dict):
            return defaults
        for key in defaults:
            defaults[key] = str(info.get(key) or "").strip()
        return defaults

    def _normalize_experience_list(self, items: Any) -> list[dict[str, Any]]:
        if not isinstance(items, list):
            return []
        result: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = {
                "school": str(item.get("school") or "").strip(),
                "company": str(item.get("company") or "").strip(),
                "name": str(item.get("name") or "").strip(),
                "major": str(item.get("major") or "").strip(),
                "position": str(item.get("position") or "").strip(),
                "role": str(item.get("role") or "").strip(),
                "degree": str(item.get("degree") or "").strip(),
                "start_date": str(item.get("start_date") or "").strip(),
                "end_date": str(item.get("end_date") or "").strip(),
                "description": str(item.get("description") or "").strip(),
            }
            # 保留有内容的条目
            if any(normalized.values()):
                result.append(normalized)
        return result

    def _dedup_and_clean(self, skills: Any) -> list[str]:
        if not isinstance(skills, list):
            return []
        seen: set[str] = set()
        result: list[str] = []
        for s in skills:
            text = str(s).strip()
            if not text:
                continue
            lower = text.lower()
            if lower not in seen:
                seen.add(lower)
                result.append(text)
        return result

    # ------------------------------------------------------------------
    # 规则提取方法
    # ------------------------------------------------------------------
    def _extract_name(self, text: str) -> str:
        # 优先匹配 "姓名：xxx"
        m = re.search(r"(?:姓名|Name)[:：\s]+([\u4e00-\u9fa5A-Za-z·\s]{2,20})", text, re.I)
        if m:
            return m.group(1).strip()
        # 取第一行较短内容
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:5]:
            if 2 <= len(line) <= 10 and not re.search(r"[:：]", line):
                return line
        return ""

    def _extract_phone(self, text: str) -> str:
        m = re.search(r"(?:电话|手机|Tel|Phone)[:：\s]*([1][3-9]\d{9})", text, re.I)
        if m:
            return m.group(1)
        # 直接匹配手机号
        m = re.search(r"(?<![\d])([1][3-9]\d{9})(?![\d])", text)
        if m:
            return m.group(1)
        return ""

    def _extract_email(self, text: str) -> str:
        m = re.search(r"(?:邮箱|Email|E-mail)[:：\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", text, re.I)
        if m:
            return m.group(1)
        m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if m:
            return m.group(0)
        return ""

    def _extract_gender(self, text: str) -> str:
        m = re.search(r"(?:性别|Gender)[:：\s]*([男女])", text, re.I)
        if m:
            return m.group(1)
        if "男" in text[:200] and "女" not in text[:200]:
            return "男"
        if "女" in text[:200] and "男" not in text[:200]:
            return "女"
        return ""

    def _extract_birth_date(self, text: str) -> str:
        # 出生年月：2004.09 或 2004-09 或 2004年9月
        m = re.search(r"(?:出生日期|出生年月|出生)[:：\s]*(\d{4})[\.\-/年](\d{1,2})", text)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}"
        return ""

    def _extract_political_status(self, text: str) -> str:
        statuses = ["中共党员", "中共预备党员", "共青团员", "群众", "民主党派", "无党派人士"]
        for s in statuses:
            if s in text:
                return s
        m = re.search(r"(?:政治面貌)[:：\s]*([^\n]{2,20})", text)
        if m:
            return m.group(1).strip()
        return ""

    def _extract_skills(self, text: str) -> list[str]:
        found = []
        for skill in _SKILL_KEYWORDS:
            escaped = re.escape(skill)
            pattern = r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9])"
            if re.search(pattern, text):
                found.append(skill)
        found = sorted(set(found), key=lambda s: text.find(s))

        # 额外从 "技能：xxx" 区域提取逗号分隔的技能
        m = re.search(r"(?:技能|专业技能|技术栈|掌握技能)[:：]([^\n]+)", text, re.I)
        if m:
            extra = [s.strip() for s in re.split(r"[,，/、;；]", m.group(1)) if s.strip()]
            found = self._dedup_and_clean(found + extra)

        return found

    def _extract_education(self, text: str) -> list[dict[str, Any]]:
        """提取教育经历。"""
        educations: list[dict[str, Any]] = []
        # 匹配格式：2023.09-2027.06 浙江工业大学 信息管理与信息系统 | 本科
        pattern = re.compile(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)\s*["  # noqa: E501
            r"\u4e00-\u9fa5A-Za-z\s·]+",
            re.M,
        )
        for m in pattern.finditer(text):
            line = m.group(0)
            school_match = re.search(r"[\u4e00-\u9fa5]{2,20}(?:大学|学院|学校|研究所)", line)
            major_match = re.search(
                r"(?:大学|学院|学校|研究所)\s*["  # noqa: E501
                r"\u4e00-\u9fa5A-Za-z\s·]{2,30}",
                line,
            )
            degree = ""
            for deg_pattern, deg in _EDUCATION_PATTERNS:
                if re.search(deg_pattern, line):
                    degree = deg
                    break
            educations.append({
                "school": school_match.group(0) if school_match else "",
                "major": major_match.group(0).replace(school_match.group(0) if school_match else "", "").strip() if major_match else "",
                "degree": degree,
                "start_date": m.group(1),
                "end_date": m.group(2),
                "description": "",
            })
        return educations

    def _extract_work_experience(self, text: str) -> list[dict[str, Any]]:
        """提取工作经历。"""
        experiences: list[dict[str, Any]] = []
        # 匹配格式：2024.10-2024.12 公司名 — 职位
        pattern = re.compile(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)\s*["  # noqa: E501
            r"\u4e00-\u9fa5A-Za-z\s·()（）—\-]+",
            re.M,
        )
        for m in pattern.finditer(text):
            line = m.group(0)
            # 过滤掉教育经历行（包含大学/学院）
            if re.search(r"大学|学院|学校|研究所", line):
                continue
            company_match = re.search(r"[\u4e00-\u9fa5A-Za-z]{2,30}(?:股份|科技|网络|信息|智能|有限公司|公司)", line)
            position_match = re.search(r"[—\-–]\s*([^\n]{2,30}?)(?:\s*[（(]|$)", line)
            experiences.append({
                "company": company_match.group(0) if company_match else "",
                "position": position_match.group(1).strip() if position_match else "",
                "start_date": m.group(1),
                "end_date": m.group(2),
                "description": "",
            })
        return experiences

    def _extract_project_experience(self, text: str) -> list[dict[str, Any]]:
        """提取项目经历。"""
        projects: list[dict[str, Any]] = []
        # 匹配格式：2025.04-2025.07 | 项目名称 — 角色
        pattern = re.compile(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)\s*[|]?\s*["  # noqa: E501
            r"\u4e00-\u9fa5A-Za-z\s·()（）—\-|]+",
            re.M,
        )
        for m in pattern.finditer(text):
            line = m.group(0)
            # 过滤掉工作/教育行
            if re.search(r"大学|学院|学校|有限公司|公司.*产品|产品助理|工程师", line):
                continue
            name_match = re.search(r"[|]\s*([^—\-|]{2,40})", line)
            role_match = re.search(r"[—\-–]\s*([^\n]{2,20}?)(?:\s*[（(]|$)", line)
            projects.append({
                "name": name_match.group(1).strip() if name_match else line.strip(),
                "role": role_match.group(1).strip() if role_match else "",
                "start_date": m.group(1),
                "end_date": m.group(2),
                "description": "",
            })
        return projects

    def _extract_awards(self, text: str) -> list[str]:
        awards: list[str] = []
        section = self._extract_section(text, ["获奖经历", "获奖情况", "荣誉", "奖项"])
        if section:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 5:
                    awards.append(line)
        return awards[:20]

    def _extract_certifications(self, text: str) -> list[str]:
        certs: list[str] = []
        section = self._extract_section(text, ["资格证书", "证书", "职业资格"])
        if section:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 2:
                    certs.append(line)
        return certs[:20]

    def _extract_language_skills(self, text: str) -> list[str]:
        langs: list[str] = []
        section = self._extract_section(text, ["外语能力", "语言能力", "英语", "CET"])
        if section:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 2:
                    langs.append(line)
        # 如果没找到专门段落，搜索 CET/雅思/托福
        if not langs:
            for m in re.finditer(r"(CET[-]?[46][:：]?\s*\d+|英语四六级|雅思\s*\d+\.?\d*|托福\s*\d+)", text, re.I):
                langs.append(m.group(0))
        return langs[:10]

    def _extract_self_evaluation(self, text: str) -> str:
        section = self._extract_section(text, ["个人优势", "自我评价", "自我描述", "个人总结"])
        if section:
            return section.strip()
        return ""

    def _extract_expected_position(self, text: str) -> str:
        m = re.search(r"(?:期望岗位|求职岗位|应聘岗位|意向岗位)[:：\s]*([^\n]{2,30})", text, re.I)
        if m:
            return m.group(1).strip()
        return ""

    def _extract_section(self, text: str, titles: list[str]) -> str:
        """按标题提取段落，直到下一个同级标题或空行结束。"""
        for title in titles:
            pattern = re.compile(rf"(?:^|\n)\s*{re.escape(title)}\s*\n", re.M)
            m = pattern.search(text)
            if m:
                start = m.end()
                # 找到下一个标题或主要分段
                next_section = re.search(r"\n\s*(?:教育背景|教育经历|工作经历|项目经历|获奖经历|获奖情况|资格证书|外语能力|自我评价|个人优势|求职意向|技能)\s*\n", text[start:], re.M)  # noqa: E501
                end = start + next_section.start() if next_section else len(text)
                return text[start:end].strip()
        return ""

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        resume_text = context.get("text") or context.get("resume_text") or ""
        return self.parse_resume(resume_text)
