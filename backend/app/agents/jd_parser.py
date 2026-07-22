import logging
import re
from typing import Any

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# 预定义技能关键词库（用于无 LLM 降级解析）
_SKILL_KEYWORDS: set[str] = {
    "Python", "Java", "JavaScript", "TypeScript", "Go", "C++", "C#", "Rust",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "SQL", "Shell", "R", "MATLAB",
    "React", "Vue.js", "Angular", "Svelte", "Next.js", "Nuxt.js", "jQuery",
    "Bootstrap", "Tailwind CSS", "Ant Design", "Element UI", "Webpack", "Vite",
    "Spring Boot", "Django", "Flask", "FastAPI", "Express", "NestJS",
    "Ruby on Rails", "Laravel", "ThinkPHP", "Gin", "Beego", "Echo",
    "ASP.NET Core", "Fastify", "Koa", "Tornado",
    "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "ClickHouse",
    "TiDB", "Oracle", "SQL Server", "SQLite", "DynamoDB", "Cassandra", "Neo4j",
    "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost", "LightGBM",
    "Hugging Face", "OpenAI API", "LangChain", "LlamaIndex", "Pandas", "NumPy",
    "Matplotlib", "Seaborn", "OpenCV", "NLTK", "spaCy", "Transformer", "CNN",
    "RNN", "GAN", "强化学习", "计算机视觉", "自然语言处理", "Prompt Engineering",
    "RAG",
    "Git", "Docker", "Kubernetes", "Jenkins", "GitLab CI", "GitHub Actions",
    "Terraform", "Ansible", "Prometheus", "Grafana", "ELK Stack", "Kafka",
    "RabbitMQ", "Nginx", "Linux", "Bash", "JIRA", "Confluence", "Postman",
    "Swagger", "Figma", "Sketch", "Adobe XD", "Markdown",
    "沟通能力", "团队协作", "项目管理", "需求分析", "时间管理", "领导力",
    "解决问题", "抗压能力", "学习能力", "演讲表达", "跨部门协作", "产品思维",
    "用户洞察", "数据驱动", "敏捷开发", "文档能力", "英语读写", "商务谈判",
    "冲突管理", "教练辅导",
}

_EXPERIENCE_PATTERNS: list[tuple[str, str]] = [
    (r"应届|在校生|实习|实习生", "应届/在校生"),
    (r"1[-—]?3年|1到3年|一年以上.{0,5}三年以下", "1-3年"),
    (r"3[-—]?5年|3到5年|三年以上.{0,5}五年以下", "3-5年"),
    (r"5[-—]?10年|5到10年|五年以上.{0,5}十年以下", "5-10年"),
    (r"10年以上|十年以上", "10年以上"),
]

_EDUCATION_PATTERNS: list[tuple[str, str]] = [
    (r"博士", "博士"),
    (r"硕士|研究生", "硕士"),
    (r"本科|学士|统招本科|全日制本科", "本科"),
    (r"大专|专科", "大专"),
]


class JDParser(BaseAgent):
    """岗位描述解析 Agent。

    将原始 JD 文本解析为结构化字段；LLM 不可用时使用规则引擎解析。
    """

    name = "jd_parser"

    def parse_jd(self, jd_text: str) -> dict[str, Any]:
        """解析 JD 文本，返回结构化结果。"""
        system_prompt = self._load_prompt()
        user_prompt = f"请解析以下岗位描述：\n\n{jd_text}"

        result = self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )

        # 如果 result 包含 simulated 说明走了降级，且基类 _simulate_response 未返回有效字段
        if result.get("simulated"):
            return self._rule_based_parse(jd_text)

        # 过滤并补充必要字段
        return self._normalize_parse_result(result, jd_text)

    def _normalize_parse_result(
        self, result: dict[str, Any], jd_text: str
    ) -> dict[str, Any]:
        """确保返回字段完整且类型正确。"""
        normalized: dict[str, Any] = {
            "title": result.get("title", ""),
            "company": result.get("company", ""),
            "required_skills": result.get("required_skills") or [],
            "experience_level": result.get("experience_level", "不限"),
            "education_level": result.get("education_level", "不限"),
            "implicit_needs": result.get("implicit_needs") or [],
        }

        for key in ("required_skills", "implicit_needs"):
            if isinstance(normalized[key], str):
                normalized[key] = [normalized[key]]
            normalized[key] = [str(x) for x in normalized[key] if x]

        if not normalized["title"]:
            normalized["title"] = self._extract_title(jd_text)
        if not normalized["company"]:
            normalized["company"] = self._extract_company(jd_text)
        if normalized["experience_level"] == "不限":
            normalized["experience_level"] = self._extract_experience(jd_text)
        if normalized["education_level"] == "不限":
            normalized["education_level"] = self._extract_education(jd_text)

        return normalized

    def _rule_based_parse(self, jd_text: str) -> dict[str, Any]:
        """无 LLM 时的规则解析。"""
        return {
            "title": self._extract_title(jd_text),
            "company": self._extract_company(jd_text),
            "required_skills": self._extract_skills(jd_text),
            "experience_level": self._extract_experience(jd_text),
            "education_level": self._extract_education(jd_text),
            "implicit_needs": self._extract_implicit_needs(jd_text),
        }

    def _extract_title(self, jd_text: str) -> str:
        lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
        if not lines:
            return ""
        # 首行若为短文本，通常包含职位名称
        first = lines[0]
        if len(first) <= 30 and (
            "招聘" in first or "诚聘" in first or "工程师" in first or "经理" in first
        ):
            return first.replace("招聘", "").replace("诚聘", "").strip("：:- ")
        # 尝试匹配 "岗位：xxx"
        m = re.search(r"(?:岗位|职位|title)[:：]\s*([^\n]{2,30})", jd_text, re.I)
        if m:
            return m.group(1).strip()
        return lines[0][:30]

    def _extract_company(self, jd_text: str) -> str:
        m = re.search(r"(?:公司|企业)[:：]\s*([^\n]{2,50})", jd_text)
        if m:
            return m.group(1).strip()
        m = re.search(r"([\u4e00-\u9fa5]{2,20}(?:科技|网络|信息|智能|互联|数字|云|创新))", jd_text)
        if m:
            return m.group(1)
        return ""

    def _extract_skills(self, jd_text: str) -> list[str]:
        found = []
        for skill in _SKILL_KEYWORDS:
            escaped = re.escape(skill)
            # 要求技能前后不能紧接字母或数字，避免 PostgreSQL 被误识别为 SQL
            pattern = r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9])"
            if re.search(pattern, jd_text):
                found.append(skill)
        # 按出现位置排序，去重
        found = sorted(set(found), key=lambda s: jd_text.find(s))
        return found

    def _extract_experience(self, jd_text: str) -> str:
        for pattern, level in _EXPERIENCE_PATTERNS:
            if re.search(pattern, jd_text):
                return level
        return "不限"

    def _extract_education(self, jd_text: str) -> str:
        for pattern, level in _EDUCATION_PATTERNS:
            if re.search(pattern, jd_text):
                return level
        return "不限"

    def _extract_implicit_needs(self, jd_text: str) -> list[str]:
        needs: list[str] = []
        if re.search(r"加班|996|弹性工作", jd_text):
            needs.append("接受加班或弹性工作")
        if re.search(r"沟通|协调|跨部门", jd_text):
            needs.append("良好的沟通协调能力")
        if re.search(r"英语|CET|四级|六级|雅思|托福", jd_text):
            needs.append("英语能力")
        if re.search(r"抗压|压力|快节奏", jd_text):
            needs.append("抗压能力")
        if re.search(r"团队管理|带领团队|管理经验", jd_text):
            needs.append("团队管理经验")
        return needs

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent 抽象方法实现。"""
        jd_text = context.get("text") or context.get("jd_text") or ""
        return self.parse_jd(jd_text)
