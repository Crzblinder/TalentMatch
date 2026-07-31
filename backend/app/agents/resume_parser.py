"""简历解析 Agent。"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.base import BaseAgent
from app.agents.jd_parser import _EDUCATION_PATTERNS, _SKILL_KEYWORDS

logger = logging.getLogger(__name__)

# 扩展简历专用技能词库，覆盖项目/实习描述中的常见能力
_RESUME_SKILL_KEYWORDS: set[str] = _SKILL_KEYWORDS | {
    "A/B测试",
    "BM25",
    "BGE",
    "ChromaDB",
    "LangGraph",
    "LoRA",
    "Multi-Agent",
    "Ollama",
    "Power Query",
    "Prompt Engineering",
    "RAG",
    "SQL",
    "Tableau",
    "TextGeneration WebUI",
    "UML",
    "Vibe Coding",
    "产品架构设计",
    "产品设计",
    "可用性测试",
    "大模型部署",
    "数据闭环",
    "数据工程",
    "数据驱动",
    "旅程地图",
    "无障碍审计",
    "用户画像",
    "用户洞察",
    "需求分析",
    "混合检索",
    "渐进式披露",
}


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
            "education": self._normalize_education_list(result.get("education") or []),
            "work_experience": self._normalize_work_experience_list(
                result.get("work_experience") or []
            ),
            "project_experience": self._normalize_project_experience_list(
                result.get("project_experience") or []
            ),
            "competition_experience": self._normalize_competition_list(
                result.get("competition_experience") or []
            ),
            "publications": self._normalize_publication_list(result.get("publications") or []),
            "portfolio": self._normalize_portfolio_list(result.get("portfolio") or []),
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

        # 语言能力/自我评价若为空，用规则补充
        if not normalized["language_skills"]:
            normalized["language_skills"] = self._extract_language_skills(resume_text)
        if not normalized["self_evaluation"]:
            normalized["self_evaluation"] = self._extract_self_evaluation(resume_text)

        # 教育、工作、项目经历若为空，用规则补充
        if not normalized["education"]:
            normalized["education"] = self._extract_education(resume_text)
        if not normalized["work_experience"]:
            normalized["work_experience"] = self._extract_work_experience(resume_text)
        if not normalized["project_experience"]:
            normalized["project_experience"] = self._extract_project_experience(resume_text)

        # 赛事、论文、作品附件若为空，用规则补充
        if not normalized["competition_experience"]:
            normalized["competition_experience"] = self._extract_competition_experience(
                resume_text
            )
        if not normalized["publications"]:
            normalized["publications"] = self._extract_publications(resume_text)
        if not normalized["portfolio"]:
            normalized["portfolio"] = self._extract_portfolio(resume_text)

        # 求职意向若为空，用规则补充
        ji = normalized["job_intention"]
        if not ji.get("expected_position"):
            ji["expected_position"] = self._extract_expected_position(resume_text)

        # 教育经历中学历字段为空时，从原始文本补充
        for edu in normalized["education"]:
            if not edu.get("degree"):
                edu["degree"] = self._extract_degree_from_text(resume_text)

        # 最高学历未解析时，从教育经历推断
        basic = normalized["basic_info"]
        if not basic.get("highest_education") and normalized["education"]:
            basic["highest_education"] = self._infer_highest_education(normalized["education"])
        if not basic.get("highest_education"):
            basic["highest_education"] = self._extract_degree_from_text(resume_text)

        return normalized

    # ------------------------------------------------------------------
    # 规则引擎兜底
    # ------------------------------------------------------------------
    def _rule_based_parse(self, resume_text: str) -> dict[str, Any]:
        """无 LLM 时的规则解析。"""
        education = self._extract_education(resume_text)
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
                # 大疆网申字段扩展
                "highest_education": self._infer_highest_education(education),
                "recruitment_source": "",
                "other_intended_position": "",
                "accept_city_adjustment": "",
                "current_country": "",
                "current_location": "",
            },
            "education": education,
            "work_experience": self._extract_work_experience(resume_text),
            "project_experience": self._extract_project_experience(resume_text),
            "competition_experience": self._extract_competition_experience(resume_text),
            "publications": self._extract_publications(resume_text),
            "portfolio": self._extract_portfolio(resume_text),
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
            # 大疆网申字段扩展
            "highest_education": "",
            "recruitment_source": "",
            "other_intended_position": "",
            "accept_city_adjustment": "",
            "current_country": "",
            "current_location": "",
        }
        if not isinstance(info, dict):
            return defaults
        uncertain_values = {"未知", "不确定", "不详", "n/a", "na"}
        for key in defaults:
            value = str(info.get(key) or "").strip()
            # 清理明显的不确定/占位值，避免误导下游填充
            if value.lower() in uncertain_values:
                value = ""
            # 婚姻状况只允许明确的值
            if key == "marriage" and value not in {"未婚", "已婚", "离异"}:
                value = ""
            # 性别只允许明确的值，避免 LLM 根据姓名推测
            if key == "gender" and value not in {"男", "女"}:
                value = ""
            defaults[key] = value
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

    def _normalize_education_list(self, items: Any) -> list[dict[str, Any]]:
        """归一化教育经历列表。"""
        if not isinstance(items, list):
            return []
        result: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = {
                "school": str(item.get("school") or "").strip(),
                "major": str(item.get("major") or "").strip(),
                "degree": str(item.get("degree") or "").strip(),
                "start_date": str(item.get("start_date") or "").strip(),
                "end_date": str(item.get("end_date") or "").strip(),
                "description": str(item.get("description") or "").strip(),
                # 大疆网申教育字段扩展
                "department": str(item.get("department") or "").strip(),
                "ranking": str(item.get("ranking") or "").strip(),
                "has_lab_experience": str(item.get("has_lab_experience") or "").strip(),
            }
            if any(normalized.values()):
                result.append(normalized)
        return result

    def _normalize_work_experience_list(self, items: Any) -> list[dict[str, Any]]:
        """归一化工作经历/实习经历列表。"""
        if not isinstance(items, list):
            return []
        result: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = {
                "company": str(item.get("company") or "").strip(),
                "position": str(item.get("position") or "").strip(),
                "start_date": str(item.get("start_date") or "").strip(),
                "end_date": str(item.get("end_date") or "").strip(),
                "description": str(item.get("description") or "").strip(),
            }
            if any(normalized.values()):
                result.append(normalized)
        return result

    def _normalize_project_experience_list(self, items: Any) -> list[dict[str, Any]]:
        """归一化项目经历列表。"""
        if not isinstance(items, list):
            return []
        result: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = {
                "name": str(item.get("name") or "").strip(),
                "role": str(item.get("role") or "").strip(),
                "start_date": str(item.get("start_date") or "").strip(),
                "end_date": str(item.get("end_date") or "").strip(),
                "description": str(item.get("description") or "").strip(),
            }
            if any(normalized.values()):
                result.append(normalized)
        return result

    def _normalize_competition_list(self, items: Any) -> list[dict[str, Any]]:
        """归一化赛事/竞赛经历列表。"""
        if not isinstance(items, list):
            return []
        result: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = {
                "start_date": str(item.get("start_date") or "").strip(),
                "end_date": str(item.get("end_date") or "").strip(),
                "competition_name": str(item.get("competition_name") or "").strip(),
                "other_competition_name": str(
                    item.get("other_competition_name") or ""
                ).strip(),
                "description": str(item.get("description") or "").strip(),
            }
            if any(normalized.values()):
                result.append(normalized)
        return result

    def _normalize_publication_list(self, items: Any) -> list[dict[str, Any]]:
        """归一化论文/期刊列表。"""
        if not isinstance(items, list):
            return []
        result: list[dict[str, Any]] = []
        for item in items:
            if isinstance(item, dict):
                title = str(item.get("title") or "").strip()
            else:
                title = str(item).strip()
            if title:
                result.append({"title": title})
        return result

    def _normalize_portfolio_list(self, items: Any) -> list[dict[str, Any]]:
        """归一化作品附件列表。"""
        if not isinstance(items, list):
            return []
        result: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized = {
                "file_url": str(item.get("file_url") or "").strip(),
                "link_url": str(item.get("link_url") or "").strip(),
            }
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

    def _infer_highest_education(self, educations: list[dict[str, Any]]) -> str:
        """根据教育经历列表推断最高学历。"""
        level_order = {"博士": 4, "硕士": 3, "本科": 2, "大专": 1}
        best = ""
        best_score = 0
        for edu in educations:
            degree = str(edu.get("degree") or "").strip()
            score = level_order.get(degree, 0)
            if score > best_score:
                best_score = score
                best = degree
        return best

    def _extract_degree_from_text(self, text: str) -> str:
        """从全文中提取最高学历（优先本科、硕士、博士、大专顺序中最高者）。"""
        level_order = {"博士": 4, "硕士": 3, "本科": 2, "大专": 1}
        best = ""
        best_score = 0
        for pattern, level in _EDUCATION_PATTERNS:
            if re.search(pattern, text):
                score = level_order.get(level, 0)
                if score > best_score:
                    best_score = score
                    best = level
        return best

    # ------------------------------------------------------------------
    # 规则提取方法
    # ------------------------------------------------------------------
    def _extract_name(self, text: str) -> str:
        # 优先匹配 "姓名：xxx"，限制在同一行内，避免捕获后续内容
        m = re.search(
            r"(?:姓名|Name)[:：\s]+([\u4e00-\u9fa5A-Za-z· ]{2,20})(?=\s|$)",
            text,
            re.I,
        )
        if m:
            return m.group(1).strip()
        # 取第一行较短内容，排除日期、邮箱、电话行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:5]:
            if 2 <= len(line) <= 10 and not re.search(r"[:：\d@]", line):
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
        # 先规范化邮箱中常见的空格，如 "3014172715 @qq .com"
        normalized = re.sub(r"([A-Za-z0-9._%+-])\s+@", r"\1@", text)
        normalized = re.sub(r"@\s+([A-Za-z0-9.-])", r"@\1", normalized)
        normalized = re.sub(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)\s+\.", r"\1.", normalized)

        email_pattern = r"(?:邮箱|Email|E-mail)[:：\s]*"
        email_pattern += r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
        m = re.search(email_pattern, normalized, re.I)
        if m:
            return m.group(1)
        m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", normalized)
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
        # 出生年月：2004.09 / 2004-09 / 2004年9月，兼容 "2004 .09" 等空格
        normalized = re.sub(r"(\d{4})\s*[\.\-/年]\s*(\d{1,2})", r"\1.\2", text)
        m = re.search(r"(?:出生日期|出生年月|出生)[:：\s]*(\d{4})[\.\-/年](\d{1,2})", normalized)
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
        for skill in _RESUME_SKILL_KEYWORDS:
            escaped = re.escape(skill)
            pattern = r"(?<![A-Za-z0-9\u4e00-\u9fa5])" + escaped + r"(?![A-Za-z0-9\u4e00-\u9fa5])"
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
        # 规范化日期范围中的空格与连接符，兼容 - – — ～ 至
        normalized = re.sub(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-–—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)",
            r"\1-\2",
            text,
        )
        # 匹配格式：2023.09-2027.06 浙江工业大学 信息管理与信息系统 | 本科
        pattern = re.compile(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-–—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)\s*[:：]?\s*[^\n]+",  # noqa: E501
            re.M,
        )
        for m in pattern.finditer(normalized):
            line = m.group(0)
            # 只保留时间后面的核心内容，截断到常见分隔符
            core = re.split(r"[|\n]", line, maxsplit=1)[0]
            school_match = re.search(r"[\u4e00-\u9fa5]{2,20}(?:大学|学院|学校|研究所)", core)
            major = ""
            if school_match:
                after_school = core[school_match.end():].strip()
                # 提取后续专业名（中文或英文，直到遇到学历词或结束）
                major_match = re.match(r"[\u4e00-\u9fa5A-Za-z\s·]{2,30}", after_school)
                if major_match:
                    major = major_match.group(0).strip()
            degree = ""
            for deg_pattern, deg in _EDUCATION_PATTERNS:
                if re.search(deg_pattern, line):
                    degree = deg
                    break
            # 必须至少包含学校或日期才保留
            if school_match or major:
                educations.append({
                    "school": school_match.group(0) if school_match else "",
                    "major": major,
                    "degree": degree,
                    "start_date": m.group(1),
                    "end_date": m.group(2),
                    "description": "",
                })
        return educations

    def _extract_work_experience(self, text: str) -> list[dict[str, Any]]:
        """提取工作经历。"""
        experiences: list[dict[str, Any]] = []
        # 规范化日期范围中的空格与连接符，兼容 - – — ～ 至
        normalized = re.sub(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-–—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)",
            r"\1-\2",
            text,
        )
        # 匹配格式：2024.10-2024.12 公司名 — 职位
        pattern = re.compile(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-–—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)\s*[^\n]+",  # noqa: E501
            re.M,
        )
        for m in pattern.finditer(normalized):
            line = m.group(0)
            # 过滤掉教育经历行（包含大学/学院/专业/CET 等）
            if re.search(r"大学|学院|学校|研究所|专业|CET|计算机二级|奖学金|毕业院校", line):
                continue
            # 去掉时间前缀与前置 "|"
            date_prefix = (
                r"^\d{4}[\.\-/]\d{1,2}\s*[~\-–—至]\s*"
                r"(\d{4}[\.\-/]\d{1,2}|至今)\s*[|]?\s*"
            )
            core = re.sub(date_prefix, "", line)
            core = re.split(r"[|\n]", core, maxsplit=1)[0]
            company_pattern = r"[\u4e00-\u9fa5A-Za-z]{2,30}"
            company_pattern += r"(?:股份|科技|网络|信息|智能|电子|有限公司|公司|分行|集团)"
            company_match = re.search(company_pattern, core)
            position_match = re.search(r"[—\-–—]\s*([^\n]{2,30}?)(?:\s*[（(]|$)", core)
            # 必须有公司名才保留，避免抓取项目/教育行
            if not company_match:
                continue
            company_name = company_match.group(0)
            position = position_match.group(1).strip() if position_match else ""
            # 过滤明显不完整的公司名（如"AI智能"缺少组织后缀）
            if len(company_name) < 6 and not re.search(
                r"(?:股份|科技|网络|信息|智能|电子|有限公司|公司|分行|集团|银行)", company_name
            ):
                continue
            experiences.append({
                "company": company_name,
                "position": position,
                "start_date": m.group(1),
                "end_date": m.group(2),
                "description": "",
            })
        return experiences

    def _extract_project_experience(self, text: str) -> list[dict[str, Any]]:
        """提取项目经历。"""
        projects: list[dict[str, Any]] = []
        # 规范化日期范围中的空格与连接符，兼容 - – — ～ 至
        normalized = re.sub(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-–—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)",
            r"\1-\2",
            text,
        )
        # 匹配格式：2025.04-2025.07 | 项目名称 — 角色
        pattern = re.compile(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-–—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)\s*[|]?\s*[^\n]+",  # noqa: E501
            re.M,
        )
        for m in pattern.finditer(normalized):
            line = m.group(0)
            # 过滤掉工作/教育行
            if re.search(r"大学|学院|学校|毕业院校|专业|CET|计算机二级|奖学金", line):
                continue
            # 过滤掉工作经历行（含公司/银行/分行等真实企业名）
            company_pattern = r"(?:股份|科技|网络|信息|智能|电子|有限公司|公司|分行|集团)"
            if re.search(company_pattern + r"[\s\u4e00-\u9fa5]*[—\-–]", line):
                continue
            core = re.split(r"[|\n]", line, maxsplit=1)[0]
            # 去掉时间前缀后的内容
            date_prefix = (
                r"^\d{4}[\.\-/]\d{1,2}\s*[~\-—至]\s*"
                r"(\d{4}[\.\-/]\d{1,2}|至今)\s*[|]?\s*"
            )
            content = re.sub(date_prefix, "", core)
            # 尝试按 "— 角色" 拆分
            role_match = re.search(r"[—\-–—]\s*([^\n]{2,30}?)(?:\s*[（(]|$)", content)
            if role_match:
                name = content[: role_match.start()].strip()
                role = role_match.group(1).strip()
            else:
                name = content.strip()
                role = ""
            # 项目名称不能是日期或纯空格
            if name and not re.match(r"^\d{4}[\.\-/]\d{1,2}", name):
                projects.append({
                    "name": name,
                    "role": role,
                    "start_date": m.group(1),
                    "end_date": m.group(2),
                    "description": "",
                })
        return projects

    def _extract_competition_experience(self, text: str) -> list[dict[str, Any]]:
        """提取赛事/竞赛经历。"""
        competitions: list[dict[str, Any]] = []
        section = self._extract_section(
            text, ["竞赛经历", "赛事经验", "比赛经历", "竞赛", "比赛"]
        )
        if not section:
            return competitions

        pattern = re.compile(
            r"(\d{4}[\.\-/]\d{1,2})\s*[~\-–—至]\s*(\d{4}[\.\-/]\d{1,2}|至今)\s*[^\n]+",  # noqa: E501
            re.M,
        )
        for m in pattern.finditer(section):
            line = m.group(0)
            name_match = re.search(
                r"(?:参加了|获得|荣获)?\s*([\u4e00-\u9fa5A-Za-z\s·+]{3,40})", line
            )
            competitions.append({
                "start_date": m.group(1),
                "end_date": m.group(2),
                "competition_name": name_match.group(1).strip() if name_match else "",
                "other_competition_name": "",
                "description": line.strip(),
            })

        # 无时间戳的兜底：按行提取
        if not competitions:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 5:
                    competitions.append({
                        "start_date": "",
                        "end_date": "",
                        "competition_name": line,
                        "other_competition_name": "",
                        "description": "",
                    })
        return competitions[:10]

    def _extract_publications(self, text: str) -> list[dict[str, Any]]:
        """提取论文/期刊。"""
        publications: list[dict[str, Any]] = []
        section = self._extract_section(
            text, ["论文", "期刊", "发表论文", "学术成果", "publications"]
        )
        if section:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 5:
                    publications.append({"title": line})
        return publications[:10]

    def _extract_portfolio(self, text: str) -> list[dict[str, Any]]:
        """提取作品链接/附件。"""
        portfolios: list[dict[str, Any]] = []
        section = self._extract_section(
            text, ["作品", "作品集", "附件", "个人主页", "github", "blog"]
        )
        if section:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 5:
                    portfolios.append({"file_url": "", "link_url": line})
        # 全文搜索 URL
        if not portfolios:
            url_pattern = re.compile(
                r"https?://[^\s\）\)）\]\}【】]+", re.I
            )
            for m in url_pattern.finditer(text):
                portfolios.append({"file_url": "", "link_url": m.group(0)})
        return portfolios[:10]

    def _extract_awards(self, text: str) -> list[str]:
        awards: list[str] = []
        # 优先从独立段落提取
        section = self._extract_section(text, ["获奖经历", "获奖情况", "荣誉", "奖项"])
        if section:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 5:
                    awards.append(line)
        # 兜底：从全文中提取常见奖项描述
        if not awards:
            award_patterns = [
                r"(?:全国|浙江省|校级|学院|国家|国际)[\u4e00-\u9fa5A-Za-z\s·+]{3,40}(?:二等奖|一等奖|三等奖|银奖|金奖|铜奖|特等奖|优秀奖|提名奖)",
                r"[\u4e00-\u9fa5A-Za-z\s·+]{3,30}(?:二等奖|一等奖|三等奖|银奖|金奖|铜奖|特等奖|优秀奖)",
            ]
            seen = set()
            for pattern in award_patterns:
                for m in re.finditer(pattern, text):
                    item = m.group(0).strip()
                    if item and item not in seen:
                        seen.add(item)
                        awards.append(item)
        return awards[:20]

    def _extract_certifications(self, text: str) -> list[str]:
        certs: list[str] = []
        # 优先从独立段落提取
        section = self._extract_section(text, ["资格证书", "证书", "职业资格"])
        if section:
            for line in section.splitlines():
                line = line.strip()
                if line and len(line) > 2:
                    certs.append(line)
        # 兜底：从全文中提取常见证书
        if not certs:
            cert_patterns = [
                r"CET[-]?\d+\s*[:：]?\s*\d+",
                r"英语四六级?\s*[:：]?\s*\d+",
                r"计算机二级",
                r"计算机三级",
                r"普通话等级",
                r"软件设计师",
                r"PMP",
                r"CFA",
            ]
            seen = set()
            for pattern in cert_patterns:
                for m in re.finditer(pattern, text, re.I):
                    item = m.group(0).strip()
                    if item and item not in seen:
                        seen.add(item)
                        certs.append(item)
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
            lang_pattern = r"(CET[-]?[46]\s*[:：]?\s*\d+|英语四六级|"
            lang_pattern += r"雅思\s*\d+\.?\d*|托福\s*\d+|英语可作为工作语言)"
            seen = set()
            for m in re.finditer(lang_pattern, text, re.I):
                item = m.group(0).strip()
                if item and item.lower() not in seen:
                    seen.add(item.lower())
                    langs.append(item)
        return langs[:10]

    def _extract_self_evaluation(self, text: str) -> str:
        section = self._extract_section(text, ["个人优势", "自我评价", "自我描述", "个人总结"])
        if section:
            return section.strip()
        # 兜底：合并简历末尾以 "|" 分隔的能力/优势行（OCR/PDF 可能在长句中间换行）
        lines = [line.strip() for line in text.splitlines()]
        summary_lines: list[str] = []
        for line in reversed(lines):
            if not line:
                continue
            if "|" in line and (
                "：" in line
                or "擅长" in line
                or "具备" in line
                or "英语" in line
                or "能力" in line
                or "经验" in line
                or "Github" in line
            ):
                summary_lines.insert(0, line)
            elif summary_lines:
                break
        if summary_lines:
            combined = " ".join(summary_lines)
            if len(combined) > 20:
                return combined
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
