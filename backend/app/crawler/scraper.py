"""真实岗位 JD 爬虫。

基于公开 RSS 源采集中文技术岗位，解析结构化字段后写入 JSON。
单个源失败仅记录日志，不影响其他源继续采集。
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.crawler.sources import SOURCES
from app.data.generator import CITIES, get_skill_pool

# Playwright 为可选依赖；未安装时国内平台抓取自动降级为空列表
try:
    from playwright.sync_api import TimeoutError as PWTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None
    PWTimeoutError = Exception

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 爬虫状态（全局单例）
_last_run_status: dict[str, Any] = {
    "last_run": None,
    "total_fetched": 0,
    "sources_ok": [],
    "sources_failed": [],
}

DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DEFAULT_RAW_JOBS_PATH = os.path.join(DEFAULT_DATA_DIR, "raw_jobs.json")
DEFAULT_SEED_JOBS_PATH = os.path.join(DEFAULT_DATA_DIR, "seed_jobs.json")

# 公开 RSS 源通常只能提供 10-50 条实时 JD；种子文件提供 80 条行业典型岗位兜底
MIN_REAL_JOBS = 30
TARGET_TOTAL_JOBS = 200

# 岗位相关强过滤词（用于从通用 RSS 中筛选出招聘帖）
_JOB_KEYWORDS: set[str] = {
    "招聘", "诚聘", "内推", "hire", "hiring", "职位", "岗位", "找工作",
    "谁在招聘", "talent",
}

_SALARY_PATTERNS: list[tuple[str, bool]] = [
    # (pattern, values_are_in_k)
    (r"(\d{1,3})[kK]\s*[-—~]+\s*(\d{1,3})[kK]", True),
    (r"(\d{1,3})\s*[-—~]+\s*(\d{1,3})[kK]", True),
    (r"(?:月薪|薪资|工资|salary)\s*[:：]?\s*(\d{4,6})\s*[-—~]+\s*(\d{4,6})", False),
    (r"(\d{4,6})\s*[-—~]+\s*(\d{4,6})\s*(?:元|人民币|RMB)", False),
]

_EXPERIENCE_PATTERNS: list[tuple[str, str]] = [
    (r"应届|在校生|实习|实习生", "应届/在校生"),
    (r"1\s*[-—~]\s*3\s*年|1到3年|一年以上.{0,5}三年以下|1年(?:及)?以上", "1-3年"),
    (r"3\s*[-—~]\s*5\s*年|3到5年|三年以上.{0,5}五年以下|3年(?:及)?以上", "3-5年"),
    (r"5\s*[-—~]\s*10\s*年|5到10年|五年以上.{0,5}十年以下|5年(?:及)?以上", "5-10年"),
    (r"10\s*年以上|十年以上", "10年以上"),
]

_EDUCATION_PATTERNS: list[tuple[str, str]] = [
    (r"博士", "博士"),
    (r"硕士|研究生", "硕士"),
    (r"本科|学士|统招本科|全日制本科", "本科"),
    (r"大专|专科", "大专"),
]

_COMPANY_PATTERNS: list[str] = [
    # 标题中“招聘/诚聘/招”前面的文本，常用于“贺乐科技招聘 PHP 工程师”
    r"(?:^|[【\]】\|])\s*([^—\-–\n【】\[\]]{2,30}?)\s*(?:招聘|诚聘|急聘|招)",
    r"\[([^\]]{2,30})\]",  # [公司名称]
    r"(?:公司|企业)[:：]\s*([^\n]{2,50})",
    r"([^\n]{2,30}?(?:科技|网络|信息|智能|互联|数字|云|创新|软件|咨询|传媒|金融|教育|医疗|游戏|电子|文化|服务|集团|股份|有限公司))",
]

# 方括号里常见的通用标签，不是公司名
_COMPANY_TAG_WORDS: set[str] = {
    "远程", "remote", "全职", "兼职", "实习", "内推", "求职", "招聘", "诚聘",
}

_COMPANY_FORBIDDEN_WORDS: set[str] = {
    "岗位", "职位", "信息", "个人", "联系", "更多", "关于", "我们", "作者",
    "来源", "详情", "内容", "未知", "公司", "开发", "后端", "前端", "服务",
    "系统", "应用", "管理", "统计", "支付", "移动", "api", "web", "app",
    "参与", "专注", "提供", "使用", "熟悉", "负责", "了解", "掌握", "面向",
    "处理", "限于", "成为", "有没有",
}


def get_status() -> dict[str, Any]:
    """返回爬虫最近一次运行状态。"""
    return _last_run_status.copy()


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    # 去除 HTML 标签与转义字符
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _is_job_related(title: str, content: str) -> bool:
    """判断 RSS 条目是否与招聘相关。

    先匹配强关键词，再使用多信号打分，避免把社区讨论误判为岗位。
    """
    text = f"{title} {content}".lower()
    title_lower = title.lower()

    # 明显的非招聘内容：VPN/翻墙/机场广告等
    spam_terms = {"梯子", "vpn", "翻墙", "机场", "加速器", "shadowrocket", "clash"}
    if any(term in text for term in spam_terms):
        return False

    # 社区讨论、经验分享、广告等明显非岗位内容
    non_job_terms = {
        "面经", "面试经验", "投了好几天", "淘宝", "合伙人", "客服",
        "招聘已结束", "ontolog", "本体论",
    }
    if any(term in text for term in non_job_terms):
        return False

    # 强关键词
    if any(kw in text for kw in _JOB_KEYWORDS):
        return True

    # 标题专属招聘标识
    title_job_terms = {"[求职]", "[招聘]", "[内推]", "remote", "全职", "兼职", "实习"}
    if any(term in title_lower for term in title_job_terms):
        return True

    # 标题中出现薪资范围是强信号
    if re.search(r"\d{1,3}[kK]\s*[-—~]", title) or re.search(r"\d{4,6}\s*[-—~]", title):
        return True

    # 多弱信号打分
    score = 0
    if "工程师" in title_lower or "developer" in title_lower or "engineer" in title_lower:
        score += 2
    if "开发" in title_lower:
        score += 1
    if "远程" in text or "remote" in text:
        score += 1
    if "寻找" in title_lower and ("工程师" in title_lower or "开发" in title_lower):
        return True
    if "招" in title_lower and ("工程师" in title_lower or "开发" in title_lower):
        score += 1

    return score >= 2


def _extract_salary(text: str) -> tuple[int | None, int | None]:
    for pattern, in_k in _SALARY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            low, high = int(match.group(1)), int(match.group(2))
            if in_k:
                low *= 1000
                high *= 1000
            return min(low, high), max(low, high)
    return None, None


def _extract_experience(text: str) -> str:
    for pattern, level in _EXPERIENCE_PATTERNS:
        if re.search(pattern, text):
            return level
    return ""


def _extract_education(text: str) -> str:
    for pattern, level in _EDUCATION_PATTERNS:
        if re.search(pattern, text):
            return level
    return ""


def _extract_city(text: str) -> str:
    # 优先匹配多个城市名中最长的一个，避免“北京”误匹配“北北京京”
    found: list[tuple[int, str]] = []
    for city in CITIES:
        for match in re.finditer(re.escape(city), text):
            found.append((match.start(), city))
    if not found:
        return ""
    found.sort()
    # 去重并保持出现顺序
    seen: set[str] = set()
    result: list[str] = []
    for _, city in found:
        if city not in seen:
            seen.add(city)
            result.append(city)
    # 返回第一个出现的城市；若出现多个则用“/”连接
    return "/".join(result[:2])


def _extract_company(title: str, content: str) -> str:
    def _clean(name: str) -> str:
        name = name.strip()
        # 只取第一个分隔符前的内容，避免“Moonveil — web3 游戏工作室招聘”被拖长
        name = re.split(r"[—\-–\|｜]", name)[0].strip()
        # 清理首尾标点空白
        name = re.sub(r"^[，。！？、\s）]+|[，。！？、\s（]+$", "", name)
        return name

    def _valid(name: str) -> bool:
        name = _clean(name)
        if not (2 <= len(name) <= 50) or name.startswith("http"):
            return False
        if any(word in name for word in _COMPANY_FORBIDDEN_WORDS):
            # 允许包含“公司”等词的合法企业名称，如“某科技公司”
            if not (name.endswith("公司") and len(name) > 3):
                return False
        if any(word in name for word in _COMPANY_TAG_WORDS):
            return False
        if name in CITIES:
            return False
        if re.search(r"\d+[kK]", name) or re.fullmatch(r"[\d\-–—~]+", name):
            return False
        return True

    # 1. 优先从标题“招聘/诚聘/急聘”前面提取公司名
    m = re.search(
        r"(?:^|[【\[\]】|])\s*([^—\-–\n【】\[\]]{2,30}?)\s*(?:招聘|诚聘|急聘)",
        title,
    )
    if m and _valid(m.group(1)):
        return _clean(m.group(1))

    # 2. 标题方括号内容（排除城市/远程/求职等标签）
    for m in re.finditer(r"\[([^\]]{2,30})\]", title):
        if _valid(m.group(1)):
            return _clean(m.group(1))

    # 3. 正文中的显式“公司/企业：”
    text = content or ""
    m = re.search(r"(?:公司|企业)[:：]\s*([^\n]{2,50})", text)
    if m and _valid(m.group(1)):
        return _clean(m.group(1))

    # 4. 正文中带企业后缀的名称（非贪婪，取第一个命中）
    for m in re.finditer(
        r"([^\n]{2,30}?(?:科技|网络|信息|智能|互联|数字|云|创新|软件|咨询|传媒|金融|教育|医疗|游戏|电子|文化|服务|集团|股份|有限公司))",
        text,
    ):
        if _valid(m.group(1)):
            return _clean(m.group(1))

    return ""


def _build_skill_matcher(
    skill_pool: list[tuple[str, str, list[str]]],
) -> list[tuple[str, list[str]]]:
    """构造技能匹配表：[(技能名, [所有匹配形式]), ...]。"""
    matcher = []
    for name, _category, aliases in skill_pool:
        forms = [name] + aliases
        # 去重并保持顺序
        forms = sorted(set(forms), key=lambda x: forms.index(x))
        matcher.append((name, forms))
    return matcher


def _extract_skills(
    text: str,
    skill_pool: list[tuple[str, str, list[str]]] | None = None,
) -> list[str]:
    if skill_pool is None:
        skill_pool = get_skill_pool()
    matcher = _build_skill_matcher(skill_pool)
    found: list[tuple[int, str]] = []
    seen: set[str] = set()
    for skill_name, forms in matcher:
        for form in forms:
            escaped = re.escape(form)
            # 词边界：避免 SQL 被 PostgreSQL 中的 SQL 误匹配
            pattern = r"(?<![A-Za-z0-9+.#_])" + escaped + r"(?![A-Za-z0-9+.#_])"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if skill_name not in seen:
                    seen.add(skill_name)
                    found.append((match.start(), skill_name))
                break
    found.sort()
    return [name for _, name in found]


def _parse_rss_atom_entries(content: bytes) -> list[dict[str, Any]]:
    """使用 feedparser 或 xml.etree 解析 RSS/Atom entries。"""
    try:
        import feedparser

        feed = feedparser.parse(content)
        entries = []
        for entry in feed.entries:
            title = _normalize_text(entry.get("title", ""))
            summary = _normalize_text(entry.get("summary", entry.get("description", "")))
            content_value = _normalize_text(
                entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            )
            body = content_value or summary
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))
            entries.append({
                "title": title,
                "content": body,
                "link": link,
                "published_at": published,
            })
        return entries
    except Exception as exc:
        logger.warning("feedparser 解析失败，回退到 xml.etree: %s", exc)

    try:
        from xml.etree import ElementTree as ET

        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = []
        for entry in (
            root.findall("atom:entry", ns)
            or root.findall(".//item")
            or root.findall("entry")
        ):
            title = _normalize_text(
                entry.findtext("atom:title", "", ns) or entry.findtext("title", "")
            )
            body = _normalize_text(
                entry.findtext("atom:content", "", ns)
                or entry.findtext("content", "", default="")
                or entry.findtext("atom:summary", "", ns)
                or entry.findtext("summary", "", default="")
                or entry.findtext("description", "", default="")
            )
            link = ""
            link_el = entry.find("atom:link", ns) or entry.find("link")
            if link_el is not None:
                link = link_el.get("href", "") or link_el.text or ""
            published = (
                entry.findtext("atom:published", "", ns)
                or entry.findtext("published", "")
                or entry.findtext("pubDate", "")
                or entry.findtext("updated", "")
            )
            entries.append({
                "title": title,
                "content": body,
                "link": link,
                "published_at": published,
            })
        return entries
    except Exception as exc:
        logger.warning("xml.etree 解析失败: %s", exc)
        return []


class JobScraper:
    """公开 RSS 岗位爬虫，采集后返回结构化 JD 列表。"""

    def __init__(self, timeout: float = 20.0, delay: float = 1.5):
        self.timeout = timeout
        self.delay = delay
        self.skill_pool = get_skill_pool()

    async def fetch_all(self) -> list[dict[str, Any]]:
        """遍历所有数据源采集岗位，去重后返回统一格式的 JD 列表。"""
        all_items: list[dict[str, Any]] = []
        sources_ok: list[str] = []
        sources_failed: list[str] = []

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for idx, source in enumerate(SOURCES):
                try:
                    items = await self._fetch_source(client, source)
                    if items is not None:
                        all_items.extend(items)
                        sources_ok.append(source["name"])
                        logger.info("源 %s 采集到 %d 条", source["name"], len(items))
                    else:
                        sources_failed.append(source["name"])
                except Exception as e:
                    sources_failed.append(source["name"])
                    logger.warning("源 %s 采集失败: %s", source["name"], e, exc_info=True)
                # 源之间短暂延迟，避免对 RSS 服务器造成压力
                if idx < len(SOURCES) - 1:
                    await asyncio.sleep(self.delay)

        # 基于 title + link 去重
        seen_keys: set[str] = set()
        unique_items: list[dict[str, Any]] = []
        for item in all_items:
            key = f"{item.get('title', '')}::{item.get('source_url', '')}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique_items.append(item)

        _last_run_status["last_run"] = datetime.now(timezone.utc).isoformat()
        _last_run_status["total_fetched"] = len(unique_items)
        _last_run_status["sources_ok"] = sources_ok
        _last_run_status["sources_failed"] = sources_failed

        return unique_items

    async def _fetch_source(
        self, client: httpx.AsyncClient, source: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """根据数据源类型分发采集。"""
        source_type = source.get("type", "rss")
        if source_type == "rss":
            return await self._fetch_rss(client, source)
        if source_type == "seed":
            return await self._fetch_seed(source)
        if source_type == "domestic_web":
            return await self._fetch_domestic_web(source)
        logger.warning("未知数据源类型: %s", source_type)
        return None

    async def _fetch_rss(
        self, client: httpx.AsyncClient, source: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """采集 RSS/Atom 源。"""
        resp = await client.get(
            source["url"],
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, */*",
            },
        )
        resp.raise_for_status()

        if source["parser"] == "rss_atom":
            entries = _parse_rss_atom_entries(resp.content)
            parsed = []
            requires_filter = source.get("requires_filter", True)
            for entry in entries:
                title = entry.get("title", "")
                content = entry.get("content", "")
                # 通用 RSS 源需要过滤出招聘相关内容；专用岗位源可跳过过滤
                if requires_filter and not _is_job_related(title, content):
                    continue
                # 跳过无实质内容的条目
                if not title or not content:
                    continue
                parsed.append(self._parse_job(entry, source["name"]))
            return parsed
        return None

    async def _fetch_seed(self, source: dict[str, Any]) -> list[dict[str, Any]]:
        """加载本地种子 JSON 文件。"""
        path = source.get("path")
        if not path:
            return []
        if not os.path.isabs(path):
            path = os.path.join(DEFAULT_DATA_DIR, path)
        return load_jobs(path)

    async def _fetch_domestic_web(
        self,
        source: dict[str, Any],
        keyword: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        """抓取国内招聘平台公开列表页（Playwright）。"""
        settings = get_settings()
        if not settings.domestic_crawler_enabled or not source.get("enabled"):
            logger.info("国内平台源 %s 未启用，跳过", source["name"])
            return []

        loop = asyncio.get_running_loop()
        try:
            raw_jobs = await loop.run_in_executor(
                None, _fetch_domestic_web_sync, source, keyword, location
            )
        except Exception as exc:
            logger.warning("国内平台源 %s 抓取失败: %s", source["name"], exc)
            return []

        converted: list[dict[str, Any]] = []
        for raw in raw_jobs:
            try:
                converted.append(self._convert_domestic_job(raw, source["name"]))
            except Exception as exc:
                logger.warning("转换国内平台岗位失败: %s", exc)
        return converted

    def _convert_domestic_job(
        self, raw: dict[str, Any], source_name: str
    ) -> dict[str, Any]:
        """将国内平台解析结果转换为统一 JD 结构。"""
        title = raw.get("title", "")
        company = raw.get("company", "")
        location = raw.get("location", "")
        salary_text = raw.get("salary", "")
        description = raw.get("description", "")
        full_text = f"{title}\n{company}\n{location}\n{salary_text}\n{description}"

        salary_min, salary_max = _extract_salary(salary_text)
        experience = _extract_experience(full_text)
        education = _extract_education(full_text)

        if not experience:
            experience = "不限"
        if not education:
            education = "不限"
        if salary_min is None or salary_max is None:
            salary_min, salary_max = _default_salary(experience)

        city = _extract_city(full_text) or location
        if not city:
            city = "未知"

        return {
            "title": title or "未命名岗位",
            "company_name": company or source_name.replace("_", " ").title(),
            "city": city,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience_level": experience,
            "education_level": education,
            "required_skills": _extract_skills(full_text, self.skill_pool),
            "description": description,
            "source": source_name,
            "source_url": raw.get("url", ""),
            "published_at": raw.get("published_at", ""),
        }

    def _parse_job(self, entry: dict[str, Any], source_name: str) -> dict[str, Any]:
        """将 RSS entry 解析为结构化 JD。"""
        title = entry.get("title", "")
        content = entry.get("content", "")
        full_text = f"{title}\n{content}"

        salary_min, salary_max = _extract_salary(full_text)
        experience = _extract_experience(full_text)
        education = _extract_education(full_text)
        city = _extract_city(full_text)
        company = _extract_company(title, content)
        skills = _extract_skills(full_text, self.skill_pool)

        # 默认公司名：使用来源站点名
        if not company:
            company = source_name.replace("_", " ").title()

        # 默认经验/学历
        if not experience:
            experience = "不限"
        if not education:
            education = "不限"
        # 默认薪资：根据经验给一个大致范围
        if salary_min is None or salary_max is None:
            salary_min, salary_max = _default_salary(experience)

        return {
            "title": title or "未命名岗位",
            "company_name": company,
            "city": city or "未知",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience_level": experience,
            "education_level": education,
            "required_skills": skills,
            "description": content or title,
            "source": source_name,
            "source_url": entry.get("link", ""),
            "published_at": entry.get("published_at", ""),
        }


def _default_salary(experience: str) -> tuple[int, int]:
    defaults = {
        "应届/在校生": (6000, 12000),
        "1-3年": (12000, 22000),
        "3-5年": (20000, 35000),
        "5-10年": (35000, 60000),
        "10年以上": (60000, 100000),
    }
    return defaults.get(experience, (15000, 30000))


# ---------------------------------------------------------------------------
# 国内招聘平台抓取与解析
# ---------------------------------------------------------------------------
def _build_domestic_search_url(
    source: dict[str, Any], keyword: str | None, location: str | None
) -> str:
    """根据 source 配置构造国内平台搜索 URL。"""
    kw = (keyword or source.get("keyword", "Python")).strip()
    city_code = source.get("city_code", "")
    if location:
        city_code = source.get("city_code_map", {}).get(location, city_code)
    return source["search_url_template"].format(keyword=kw, city=city_code)


def _first_text(tag: Any, *selectors: str) -> str:
    """按优先级选择第一个非空文本。"""
    for selector in selectors:
        el = tag.select_one(selector)
        if el is not None:
            text = el.get_text(strip=True)
            if text:
                return text
    return ""


def _parse_boss_job(element: Any) -> dict[str, Any]:
    """解析 Boss 直聘岗位卡片元素。"""
    title = _first_text(
        element, ".job-name", ".job-title", "[class*='job-name']", "h3", "a"
    )
    company = _first_text(
        element, ".company-name", "[class*='company-name']"
    )
    salary = _first_text(
        element, ".salary", "[class*='salary']"
    )
    location = _first_text(
        element, ".job-area", "[class*='job-area']", "[class*='area']"
    )
    link_el = element.select_one("a[href]")
    url = ""
    if link_el is not None:
        href = link_el.get("href", "")
        if href:
            url = urljoin("https://www.zhipin.com", href)

    description = " | ".join(
        part for part in [title, company, salary, location] if part
    )
    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "url": url,
        "description": description,
        "published_at": "",
    }


def _parse_zhilian_job(element: Any) -> dict[str, Any]:
    """解析智联招聘岗位卡片元素。"""
    title = _first_text(
        element,
        ".jobinfo__name",
        "[class*='jobName']",
        "[class*='job-name']",
        "h3",
        "a",
    )
    company = _first_text(
        element,
        ".company__name",
        "[class*='company_name']",
        "[class*='company-name']",
    )
    salary = _first_text(
        element, ".jobinfo__salary", "[class*='salary']"
    )
    location = _first_text(
        element,
        ".jobinfo__area",
        "[class*='address']",
        "[class*='area']",
    )
    link_el = element.select_one("a[href]")
    url = ""
    if link_el is not None:
        href = link_el.get("href", "")
        if href:
            url = urljoin("https://www.zhaopin.com", href)

    description = " | ".join(
        part for part in [title, company, salary, location] if part
    )
    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "url": url,
        "description": description,
        "published_at": "",
    }


def _get_domestic_parser(platform: str) -> Any:
    """根据 platform 字段返回对应解析函数。"""
    if platform == "boss":
        return _parse_boss_job
    if platform == "zhilian":
        return _parse_zhilian_job
    return None


def _parse_domestic_webpage(
    html_content: str, source: dict[str, Any]
) -> list[dict[str, Any]]:
    """解析国内平台列表页 HTML，返回统一字段的岗位列表。"""
    soup = BeautifulSoup(html_content, "html.parser")
    parse_func = _get_domestic_parser(source.get("platform", ""))
    if parse_func is None:
        logger.warning("未知国内平台: %s", source.get("platform"))
        return []

    selectors = source.get("job_selector") or ["div"]
    if not selectors:
        selectors = ["div"]

    jobs: list[dict[str, Any]] = []
    for el in soup.select(", ".join(selectors)):
        try:
            parsed = parse_func(el)
            if parsed and parsed.get("title"):
                jobs.append(parsed)
        except Exception as exc:
            logger.warning("解析岗位元素失败: %s", exc)
    return jobs


def _fetch_domestic_web_sync(
    source: dict[str, Any],
    keyword: str | None = None,
    location: str | None = None,
) -> list[dict[str, Any]]:
    """同步执行 Playwright 抓取（应在线程池中调用）。"""
    if sync_playwright is None:
        logger.warning("Playwright 未安装，跳过国内平台源 %s", source["name"])
        return []

    settings = get_settings()
    url = _build_domestic_search_url(source, keyword, location)
    logger.info("开始抓取国内平台源 %s: %s", source["name"], url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.playwright_headless)
        context = browser.new_context(
            user_agent=_USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            delay = max(0, settings.domestic_crawler_delay_ms)
            page.wait_for_timeout(delay)
            for selector in source.get("job_selector") or []:
                try:
                    page.wait_for_selector(selector, timeout=15000)
                    break
                except PWTimeoutError:
                    continue
            html_content = page.content()
        except Exception as exc:
            logger.warning("国内平台源 %s 页面抓取失败: %s", source["name"], exc)
            return []
        finally:
            context.close()
            browser.close()

    return _parse_domestic_webpage(html_content, source)


async def scrape_domestic_jobs(
    keyword: str | None = None, location: str | None = None
) -> list[dict[str, Any]]:
    """按需抓取所有启用的国内平台岗位（供 MCP / 工具调用）。"""
    settings = get_settings()
    if not settings.domestic_crawler_enabled:
        return []

    scraper = JobScraper()
    all_jobs: list[dict[str, Any]] = []
    for source in SOURCES:
        if source.get("type") != "domestic_web":
            continue
        try:
            jobs = await scraper._fetch_domestic_web(source, keyword, location)
            all_jobs.extend(jobs)
        except Exception as exc:
            logger.warning("国内平台源 %s 抓取失败: %s", source["name"], exc)
    return all_jobs


def save_jobs(jobs: list[dict[str, Any]], path: str | None = None) -> str:
    """将岗位列表保存为 JSON 文件。"""
    if path is None:
        path = DEFAULT_RAW_JOBS_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    return path


def load_jobs(path: str | None = None) -> list[dict[str, Any]]:
    """从 JSON 文件加载岗位列表。"""
    if path is None:
        path = DEFAULT_RAW_JOBS_PATH
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("加载 %s 失败: %s", path, exc)
        return []


async def _scrape_and_save(path: str | None = None) -> list[dict[str, Any]]:
    scraper = JobScraper()
    jobs = await scraper.fetch_all()
    save_jobs(jobs, path)
    return jobs


async def scrape_jobs(path: str | None = None) -> list[dict[str, Any]]:
    """公开入口：采集所有数据源并保存。"""
    return await _scrape_and_save(path)


def _load_seed_jobs(path: str | None = None) -> list[dict[str, Any]]:
    """加载人工整理的行业典型岗位种子数据。"""
    if path is None:
        path = DEFAULT_SEED_JOBS_PATH
    return load_jobs(path)


def _merge_jobs(*job_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """合并多个岗位列表，按 title + company_name + source_url 去重。"""
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for jobs in job_lists:
        for job in jobs:
            key = "|".join([
                job.get("title", ""),
                job.get("company_name", ""),
                job.get("source_url", ""),
            ])
            if key in seen:
                continue
            seen.add(key)
            merged.append(job)
    return merged


def fetch_real_jobs(
    min_count: int = MIN_REAL_JOBS,
    target_total: int = TARGET_TOTAL_JOBS,
    save_path: str | None = None,
    force_fetch: bool = False,
) -> list[dict[str, Any]]:
    """获取真实 JD 数据。

    数据来源优先级：
    1. 已保存的 RSS 采集结果（raw_jobs.json）
    2. 人工整理的行业典型岗位种子（seed_jobs.json）
    3. 在线 RSS 爬虫实时采集

    返回合并去重后的真实岗位列表（不补充生成数据）。
    """
    import asyncio

    # 1. 加载种子数据作为稳定基础
    seed_jobs = _load_seed_jobs()
    logger.info("加载 %d 条种子 JD", len(seed_jobs))

    # 2. 加载/采集 RSS 数据
    rss_jobs: list[dict[str, Any]] = []
    if not force_fetch:
        rss_jobs = load_jobs(save_path)
        logger.info("加载 %d 条 RSS 缓存 JD", len(rss_jobs))

    if len(seed_jobs) + len(rss_jobs) < min_count or force_fetch:
        try:
            fetched = asyncio.run(_scrape_and_save(save_path))
            rss_jobs = fetched
        except Exception as exc:
            logger.warning("在线采集失败: %s", exc)
            if not rss_jobs:
                rss_jobs = load_jobs(save_path)

    # 3. 合并去重：RSS 数据优先（更新鲜），种子数据兜底
    jobs = _merge_jobs(rss_jobs, seed_jobs)
    logger.info(
        "合并后共 %d 条真实 JD（RSS=%d, seed=%d）", len(jobs), len(rss_jobs), len(seed_jobs)
    )
    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio

    fetched = asyncio.run(_scrape_and_save())
    print(f"采集到 {len(fetched)} 条真实 JD，已保存至 {DEFAULT_RAW_JOBS_PATH}")
    for job in fetched[:3]:
        print("-", job["title"], "|", job["company_name"], "|", job["city"], "|", job["source"])
