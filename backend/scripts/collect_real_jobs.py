# ruff: noqa: E501
"""综合数据采集脚本：从多个公开源采集真实岗位 JD，清洗去重后生成 300+ 条数据。

数据源：
1. V2EX 酷工作 RSS (中文技术岗位)
2. Ruby China RSS
3. LearnKu (Python/Laravel/Go) RSS
4. Remote OK JSON API (国际远程岗位)
5. Hacker News Jobs RSS
6. Python.org Jobs RSS
7. WeWorkRemotely RSS (远程岗位)
8. 已有 seed_jobs.json (人工整理行业典型岗位)

输出：backend/data/real_jobs_collected.json (300+ 条清洗后的真实岗位)
"""

import asyncio
import html
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import httpx

# 项目路径
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.crawler.scraper import (
    JobScraper,
    _extract_city,
    _extract_company,
    _extract_education,
    _extract_experience,
    _extract_salary,
    _extract_skills,
    _is_job_related,
    _normalize_text,
    _default_salary,
)
from app.crawler.sources import SOURCES
from app.data.generator import CITIES, get_skill_pool

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DATA_DIR = os.path.join(BACKEND_DIR, "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "real_jobs_collected.json")

# 技能池用于技能提取
SKILL_POOL = get_skill_pool()


# --- 各数据源采集器 ---

async def fetch_v2ex_rss(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """V2EX 酷工作 RSS"""
    try:
        scraper = JobScraper()
        items = await scraper._fetch_rss(client, SOURCES[0])
        logger.info("V2EX: %d 条", len(items or []))
        return items or []
    except Exception as e:
        logger.warning("V2EX 采集失败: %s", e)
        return []


async def fetch_ruby_china_rss(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Ruby China RSS"""
    try:
        scraper = JobScraper()
        items = await scraper._fetch_rss(client, SOURCES[1])
        logger.info("Ruby China: %d 条", len(items or []))
        return items or []
    except Exception as e:
        logger.warning("Ruby China 采集失败: %s", e)
        return []


async def fetch_learnku_feeds(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """LearnKu Python/Laravel/Go RSS"""
    all_items = []
    for source in SOURCES[2:5]:
        try:
            scraper = JobScraper()
            items = await scraper._fetch_rss(client, source)
            all_items.extend(items or [])
        except Exception as e:
            logger.warning("LearnKu %s 采集失败: %s", source["name"], e)
    logger.info("LearnKu 合计: %d 条", len(all_items))
    return all_items


async def fetch_remoteok(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Remote OK JSON API"""
    try:
        resp = await client.get(
            "https://remoteok.com/api",
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
        data = resp.json()
        # 第一个元素是元信息，跳过
        jobs_raw = data[1:] if data and isinstance(data[0], dict) and "api" in str(data[0]) else data
        jobs = []
        for item in jobs_raw:
            if not isinstance(item, dict) or not item.get("position"):
                continue
            title = item.get("position", "")
            company = item.get("company", "")
            tags = item.get("tags", [])
            location = item.get("location", "Remote")
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            description = _normalize_text(item.get("description", ""))
            full_text = f"{title}\n{description}\n{' '.join(tags)}"

            # 薪资处理 (RemoteOK 用 USD)
            if salary_min and salary_max:
                salary_min = int(salary_min)
                salary_max = int(salary_max)
            else:
                exp = _extract_experience(full_text) or "1-3年"
                salary_min, salary_max = _default_salary(exp)

            # 城市处理
            city = _extract_city(full_text)
            if not city and location and location != "Remote":
                # 尝试匹配中国城市
                for c in CITIES:
                    if c in location:
                        city = c
                        break
            if not city:
                city = "远程" if "remote" in location.lower() else "海外"

            # 技能提取
            skills = _extract_skills(full_text, SKILL_POOL)
            # 补充 tags 中的技能
            for tag in tags[:5]:
                tag_lower = tag.lower()
                skill_map = {s[0].lower(): s[0] for s in SKILL_POOL}
                for k, v in skill_map.items():
                    if k in tag_lower and v not in skills:
                        skills.append(v)
                        break

            jobs.append({
                "title": title,
                "company_name": company or "RemoteOK",
                "city": city,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "experience_level": _extract_experience(full_text) or "不限",
                "education_level": _extract_education(full_text) or "不限",
                "required_skills": skills[:8],
                "description": description[:500] or f"{title} at {company}. Tags: {', '.join(tags[:5])}",
                "source": "remoteok",
                "source_url": item.get("url", ""),
                "published_at": item.get("date_posted", ""),
            })
        logger.info("RemoteOK: %d 条", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("RemoteOK 采集失败: %s", e)
        return []


async def fetch_hn_jobs(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Hacker News Jobs RSS"""
    try:
        resp = await client.get(
            "https://hnrss.org/jobs",
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
        from app.crawler.scraper import _parse_rss_atom_entries
        entries = _parse_rss_atom_entries(resp.content)
        jobs = []
        for entry in entries:
            title = entry.get("title", "")
            content = entry.get("content", "")
            full_text = f"{title}\n{content}"

            company = _extract_company(title, content)
            salary_min, salary_max = _extract_salary(full_text)
            exp = _extract_experience(full_text) or "不限"
            if not salary_min or not salary_max:
                salary_min, salary_max = _default_salary(exp)

            city = _extract_city(full_text) or "海外"
            skills = _extract_skills(full_text, SKILL_POOL)

            jobs.append({
                "title": title,
                "company_name": company or "HN Jobs",
                "city": city,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "experience_level": exp,
                "education_level": _extract_education(full_text) or "不限",
                "required_skills": skills[:8],
                "description": content[:500] or title,
                "source": "hn_jobs",
                "source_url": entry.get("link", ""),
                "published_at": entry.get("published_at", ""),
            })
        logger.info("HN Jobs: %d 条", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("HN Jobs 采集失败: %s", e)
        return []


async def fetch_python_jobs(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Python.org Jobs RSS"""
    try:
        resp = await client.get(
            "https://www.python.org/jobs/feed/rss/",
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
        from app.crawler.scraper import _parse_rss_atom_entries
        entries = _parse_rss_atom_entries(resp.content)
        jobs = []
        for entry in entries:
            title = entry.get("title", "")
            content = entry.get("content", "")
            full_text = f"{title}\n{content}"

            company = _extract_company(title, content)
            salary_min, salary_max = _extract_salary(full_text)
            exp = _extract_experience(full_text) or "1-3年"
            if not salary_min or not salary_max:
                salary_min, salary_max = _default_salary(exp)

            city = _extract_city(full_text) or "海外"
            skills = _extract_skills(full_text, SKILL_POOL)
            # Python 是 Python.org 的核心技能
            if "Python" not in skills:
                skills.insert(0, "Python")

            jobs.append({
                "title": title,
                "company_name": company or "Python.org Jobs",
                "city": city,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "experience_level": exp,
                "education_level": _extract_education(full_text) or "本科",
                "required_skills": skills[:8],
                "description": content[:500] or title,
                "source": "python_jobs",
                "source_url": entry.get("link", ""),
                "published_at": entry.get("published_at", ""),
            })
        logger.info("Python.org Jobs: %d 条", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Python.org Jobs 采集失败: %s", e)
        return []


async def fetch_wwr(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """WeWorkRemotely RSS"""
    try:
        resp = await client.get(
            "https://weworkremotely.com/remote-jobs.rss",
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
        from app.crawler.scraper import _parse_rss_atom_entries
        entries = _parse_rss_atom_entries(resp.content)
        jobs = []
        for entry in entries:
            title = entry.get("title", "")
            content = entry.get("content", "")
            full_text = f"{title}\n{content}"

            # WWR 标题格式通常是 "Company: Job Title"
            company = ""
            if ":" in title:
                parts = title.split(":", 1)
                company = parts[0].strip()
                title = parts[1].strip()
            if not company:
                company = _extract_company(title, content) or "WeWorkRemotely"

            salary_min, salary_max = _extract_salary(full_text)
            exp = _extract_experience(full_text) or "不限"
            if not salary_min or not salary_max:
                salary_min, salary_max = _default_salary(exp)

            city = _extract_city(full_text) or "远程"
            skills = _extract_skills(full_text, SKILL_POOL)

            jobs.append({
                "title": title,
                "company_name": company,
                "city": city,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "experience_level": exp,
                "education_level": _extract_education(full_text) or "不限",
                "required_skills": skills[:8],
                "description": content[:500] or title,
                "source": "wwr",
                "source_url": entry.get("link", ""),
                "published_at": entry.get("published_at", ""),
            })
        logger.info("WeWorkRemotely: %d 条", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("WeWorkRemotely 采集失败: %s", e)
        return []


def load_seed_jobs() -> list[dict[str, Any]]:
    """加载已有种子数据"""
    seed_path = os.path.join(DATA_DIR, "seed_jobs.json")
    if not os.path.exists(seed_path):
        return []
    with open(seed_path, encoding="utf-8") as f:
        return json.load(f)


def clean_and_deduplicate(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """清洗去重：按 title + company_name + source_url 去重"""
    seen: set[str] = set()
    cleaned: list[dict[str, Any]] = []
    for job in jobs:
        # 确保必须字段存在
        if not job.get("title") or len(job["title"]) < 2:
            continue
        # 截断过长的描述
        if job.get("description") and len(job["description"]) > 1000:
            job["description"] = job["description"][:1000]
        # 确保薪资合法
        if job.get("salary_min") and job.get("salary_max"):
            if job["salary_min"] > job["salary_max"]:
                job["salary_min"], job["salary_max"] = job["salary_max"], job["salary_min"]
            if job["salary_min"] < 0 or job["salary_max"] < 0:
                job["salary_min"], job["salary_max"] = 6000, 15000
        else:
            exp = job.get("experience_level", "1-3年")
            s_min, s_max = _default_salary(exp)
            job["salary_min"] = s_min
            job["salary_max"] = s_max

        # 确保技能列表非空
        if not job.get("required_skills"):
            job["required_skills"] = ["沟通能力", "团队协作", "学习能力"]

        # 去重 key
        key = "|".join([
            job.get("title", "")[:50],
            job.get("company_name", "")[:30],
            job.get("source_url", "")[:100],
        ])
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(job)

    return cleaned


async def collect_all() -> list[dict[str, Any]]:
    """从所有源采集数据"""
    all_jobs: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        # 并发采集所有源
        results = await asyncio.gather(
            fetch_v2ex_rss(client),
            fetch_ruby_china_rss(client),
            fetch_learnku_feeds(client),
            fetch_remoteok(client),
            fetch_hn_jobs(client),
            fetch_python_jobs(client),
            fetch_wwr(client),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                logger.warning("采集异常: %s", result)

    # 加载种子数据
    seed_jobs = load_seed_jobs()
    logger.info("种子数据: %d 条", len(seed_jobs))
    all_jobs.extend(seed_jobs)

    # 清洗去重
    cleaned = clean_and_deduplicate(all_jobs)
    logger.info("清洗去重后: %d 条", len(cleaned))

    return cleaned


def main():
    print("=" * 60)
    print("开始采集真实岗位数据...")
    print("=" * 60)

    jobs = asyncio.run(collect_all())

    # 保存结果
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"\n采集完成！共 {len(jobs)} 条真实岗位数据")
    print(f"保存至: {OUTPUT_PATH}")

    # 统计
    sources = {}
    for job in jobs:
        src = job.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    print("\n数据源统计:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count} 条")

    # 城市分布
    cities = {}
    for job in jobs:
        city = job.get("city", "未知")
        cities[city] = cities.get(city, 0) + 1
    print("\n城市分布 (Top 10):")
    for city, count in sorted(cities.items(), key=lambda x: -x[1])[:10]:
        print(f"  {city}: {count} 条")

    print(f"\n总计: {len(jobs)} 条真实岗位数据")


if __name__ == "__main__":
    main()
