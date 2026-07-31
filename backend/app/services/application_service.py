"""网申表单自动填充与 JD 简历优化服务。"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.form_matcher import FormMatcher
from app.agents.resume_optimizer import ResumeOptimizer
from app.config import get_settings
from app.services.jd_service import JDService
from app.services.resume_service import ResumeService, should_use_fuzzy_parsing
from app.utils.content_safety import check_text_safety

logger = logging.getLogger(__name__)


def rule_based_field_value(field: dict[str, Any], profile: dict[str, Any]) -> tuple[str, str]:
    """规则引擎：根据字段关键词和简历数据快速匹配。

    Returns:
        (value, confidence)
    """
    text = " ".join(
        str(v)
        for v in [
            field.get("label", ""),
            field.get("name", ""),
            field.get("placeholder", ""),
            field.get("aria_label", ""),
        ]
    ).lower()

    basic = profile.get("basic_info") or {}
    if not basic and "name" in profile:
        basic = profile

    def _get(*keys: str) -> str:
        for key in keys:
            if isinstance(basic, dict) and basic.get(key):
                return str(basic[key])
            if isinstance(profile, dict) and profile.get(key):
                return str(profile[key])
        return ""

    # 基础信息
    if any(k in text for k in ("姓名", "名字", "name", "full name")):
        return _get("name"), "high"
    if any(k in text for k in ("手机", "电话", "phone", "mobile", "tel")):
        return _get("phone"), "high"
    if any(k in text for k in ("邮箱", "邮件", "email", "e-mail")):
        return _get("email"), "high"
    if any(k in text for k in ("性别", "gender")):
        return _get("gender"), "high"
    if any(k in text for k in ("出生", "生日", "birth", "date of birth")):
        return _get("birth_date"), "high"
    if any(k in text for k in ("政治", "面貌", "political")):
        return _get("political_status"), "high"
    if any(k in text for k in ("婚姻", "marriage", "婚否")):
        return _get("marriage"), "high"
    if any(k in text for k in ("微信", "wechat")):
        return _get("wechat"), "high"
    if any(k in text for k in ("qq", "qq号")):
        return _get("qq"), "high"
    if any(k in text for k in ("证件类型", "id card type")):
        return _get("id_card_type"), "high"
    if any(k in text for k in ("证件号码", "身份证号", "id card no")):
        return _get("id_card_no"), "high"
    if any(k in text for k in ("户籍", "户口", "hukou")):
        return _get("hukou"), "medium"
    if any(k in text for k in ("籍贯", "jiguan")):
        return _get("jiguan"), "medium"
    if any(k in text for k in ("城市", "现居", "location", "city", "当前所在地")):
        return _get("current_location", "city", "hukou", "jiguan"), "medium"
    if any(k in text for k in ("国家", "country", "当前所在国家")):
        return _get("current_country"), "medium"
    if any(k in text for k in ("最高学历", "学历", "education")):
        return _get("highest_education"), "high"
    if any(k in text for k in ("招聘来源", "来源", "source", "招聘信息来源")):
        return _get("recruitment_source"), "high"
    if any(k in text for k in ("其他意向", "other position", "其他意向职位")):
        return _get("other_intended_position"), "medium"
    if any(k in text for k in ("调剂", "accept", "是否接受", "城市调剂")):
        return _get("accept_city_adjustment"), "high"

    # 求职意向
    intention = profile.get("job_intention") or {}
    if any(k in text for k in ("期望职位", "应聘职位", "岗位", "position")):
        return intention.get("expected_position", ""), "high"
    if any(k in text for k in ("期望城市", "工作城市", "expected city")):
        return intention.get("expected_city", ""), "high"
    if any(k in text for k in ("期望薪资", "salary")):
        return intention.get("expected_salary", ""), "medium"

    # 教育经历
    education = profile.get("education") or []
    if education:
        edu = education[0]
        if any(k in text for k in ("学校", "院校", "school", "university")):
            return edu.get("school", ""), "high"
        if any(k in text for k in ("专业", "major")):
            return edu.get("major", ""), "high"
        if any(k in text for k in ("学历", "学位", "degree")):
            return edu.get("degree", ""), "high"
        if any(k in text for k in ("院系", "学院", "department")):
            return edu.get("department", ""), "high"
        if any(k in text for k in ("排名", "ranking", "成绩排名")):
            return edu.get("ranking", ""), "medium"
        if any(k in text for k in ("实验室", "lab", "实验室经历")):
            return edu.get("has_lab_experience", ""), "medium"

    # 经历类字段
    if any(k in text for k in ("项目经历", "project", "项目经验")):
        projects = profile.get("project_experience") or []
        if projects:
            desc = projects[0].get("description", "")[:120]
            return f"{projects[0].get('name', '')}: {desc}", "medium"
    if any(k in text for k in ("实习经历", "工作经历", "work", "experience")):
        works = profile.get("work_experience") or []
        if works:
            desc = works[0].get("description", "")[:120]
            return (
                f"{works[0].get('company', '')} {works[0].get('position', '')}: {desc}",
                "medium",
            )
    if any(k in text for k in ("自我评价", "个人优势", "advantage", "summary")):
        return profile.get("self_evaluation", ""), "medium"

    # 获奖、证书、语言能力
    if any(k in text for k in ("获奖", "荣誉", "award", "honor")):
        awards = profile.get("awards") or []
        return "; ".join([str(a) for a in awards[:5]]), "medium"
    if any(k in text for k in ("证书", "资格", "certification")):
        certs = profile.get("certifications") or []
        return "; ".join([str(c) for c in certs[:5]]), "medium"
    if any(k in text for k in ("语言", "外语", "language", "英语", "english")):
        langs = profile.get("language_skills") or []
        return "; ".join([str(lang) for lang in langs[:5]]), "medium"

    # 赛事经历
    if any(k in text for k in ("竞赛", "赛事", "比赛", "competition")):
        comps = profile.get("competition_experience") or []
        if comps:
            first = comps[0]
            return (
                f"{first.get('competition_name', '')} "
                f"{first.get('start_date', '')}-{first.get('end_date', '')}: "
                f"{first.get('description', '')}".strip(),
                "medium",
            )

    # 论文/期刊
    if any(k in text for k in ("论文", "期刊", "publication")):
        pubs = profile.get("publications") or []
        return "; ".join([str(p.get("title", "")) for p in pubs[:5]]), "medium"

    # 作品附件/链接
    if any(k in text for k in ("作品", "附件", "portfolio", "github", "链接")):
        portfolios = profile.get("portfolio") or []
        if portfolios:
            links = [p.get("link_url", "") for p in portfolios if p.get("link_url")]
            return "; ".join(links[:5]), "medium"

    return "", "low"


class ApplicationService:
    """网申辅助服务：表单字段匹配、JD 简历优化、求职建议搜索。"""

    def match_form_fields(
        self,
        fields: list[dict[str, Any]],
        profile: dict[str, Any],
        jd_text: str | None = None,
    ) -> dict[str, Any]:
        """调用 FormMatcher Agent 智能匹配表单字段。"""
        matcher = FormMatcher()
        return matcher.match_fields(fields, profile, jd_text)

    def optimize_resume_for_jd(
        self,
        resume_data: dict[str, Any],
        jd_text: str,
        field_order: list[str] | None = None,
    ) -> dict[str, Any]:
        """根据 JD 优化简历内容，复用现有 ResumeOptimizer Agent。"""
        optimizer = ResumeOptimizer()
        return optimizer.optimize_resume(
            resume_data=resume_data,
            jd_text=jd_text,
            field_order=field_order,
        )

    def parse_jd_for_application(
        self,
        file_bytes: bytes | None,
        filename: str,
        jd_text: str | None,
    ) -> dict[str, Any]:
        """解析用户上传的 JD 图片/文件/文本，用于网申场景。"""
        settings = get_settings()
        raw_text = ""

        if file_bytes and filename:
            ext = filename.split(".")[-1].lower() if "." in filename else ""
            if ext in ("png", "jpg", "jpeg", "webp", "gif"):
                jd_service = JDService()
                raw_text = jd_service.extract_text_from_image(file_bytes, ext, settings)
            elif ext in ("pdf", "docx", "doc"):
                resume_service = ResumeService()
                raw_text = resume_service._extract_text(file_bytes, filename)
            else:
                raw_text = file_bytes.decode("utf-8", errors="ignore")

        if jd_text:
            raw_text = f"{raw_text}\n\n{jd_text}".strip()

        if not raw_text:
            raise ValueError("请提供 JD 文件或文本")

        safety = check_text_safety(raw_text, settings)
        if not safety.get("safe", True):
            labels = safety.get("labels", [])
            raise ValueError(f"JD 内容未通过安全检测: {', '.join(labels) if labels else '未知'}")

        fuzzy = should_use_fuzzy_parsing(raw_text, "jd")
        from app.agents.jd_parser import JDParser

        parser = JDParser(prompt_variant="fresh_graduate" if fuzzy else "default")
        parsed = parser.parse_jd(raw_text)
        parsed["fuzzy"] = fuzzy
        parsed["raw_text"] = raw_text
        return parsed

    def get_application_advice(
        self,
        company: str | None,
        position: str | None,
        scene: str = "网申",
    ) -> dict[str, Any]:
        """联网搜索网申经验与建议。"""
        from app.agents.search_agent import SearchAgent

        queries = []
        if company and position:
            queries.append(f"{company} {position} {scene} 经验 面试 流程")
        elif position:
            queries.append(f"{position} {scene} 经验分享 注意事项")
        elif company:
            queries.append(f"{company} 校招 {scene} 经验")
        else:
            queries.append(f"{scene} 技巧 经验分享 应届生")

        agent = SearchAgent()
        all_results: list[dict[str, Any]] = []
        for query in queries[:2]:
            try:
                result = agent.search(
                    query=query,
                    intent="job_application",
                    top_n=5,
                    summarize=True,
                )
                all_results.append(result)
            except Exception:
                logger.exception("求职建议搜索失败: %s", query)

        # 合并去重
        seen_urls = set()
        merged_results = []
        for r in all_results:
            for item in r.get("results", []):
                url = item.get("url", "")
                if url and url in seen_urls:
                    continue
                seen_urls.add(url)
                merged_results.append(item)

        summary_parts = [r.get("summary", "") for r in all_results if r.get("summary")]
        return {
            "query": queries,
            "results": merged_results[:10],
            "summary": "\n".join(summary_parts),
        }


def profile_to_resume_format(profile: dict[str, Any]) -> dict[str, Any]:
    """将 UserSkillProfile 输出转换为简历优化所需的详细格式。"""
    result: dict[str, Any] = {
        "basic_info": profile.get("basic_info", {}),
        "education": profile.get("education", []),
        "work_experience": profile.get("work_experience", []),
        "project_experience": profile.get("project_experience", []),
        "competition_experience": profile.get("competition_experience", []),
        "publications": profile.get("publications", []),
        "portfolio": profile.get("portfolio", []),
        "awards": profile.get("awards", []),
        "certifications": profile.get("certifications", []),
        "language_skills": profile.get("language_skills", []),
        "self_evaluation": profile.get("self_evaluation", ""),
        "job_intention": profile.get("job_intention", {}),
        "skills": profile.get("skills", []),
    }
    # 兼容简化版 profile
    if not result["basic_info"] and profile.get("name"):
        result["basic_info"] = {
            "name": profile.get("name", ""),
            "phone": profile.get("phone", ""),
            "email": profile.get("email", ""),
        }
    return result
