"""单独采集国内招聘平台岗位并保存到 raw_jobs.json。"""

from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.crawler.scraper import save_jobs
from app.crawler.sources import SOURCES
from app.config import get_settings

settings = get_settings()
settings.domestic_crawler_enabled = True
settings.playwright_headless = True


async def main() -> None:
    from app.crawler.scraper import JobScraper

    scraper = JobScraper()
    all_jobs: list[dict] = []

    domestic_sources = [s for s in SOURCES if s.get("type") == "domestic_web" and s.get("enabled")]
    print(f"准备采集 {len(domestic_sources)} 个国内源...")

    for idx, source in enumerate(domestic_sources):
        try:
            keyword = source.get("keyword")
            city = source.get("city_code")
            print(f"[{idx + 1}/{len(domestic_sources)}] 采集 {source['name']} (keyword={keyword}, city={city})...")
            jobs = await scraper._fetch_domestic_web(source, keyword, city)
            print(f"  -> 解析到 {len(jobs)} 条岗位")
            all_jobs.extend(jobs)
        except Exception as exc:
            print(f"  -> 失败: {exc}")

    # 按 title+company 去重
    seen: set[tuple[str, str]] = set()
    unique_jobs: list[dict] = []
    for job in all_jobs:
        key = (job.get("title", ""), job.get("company_name", ""))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    print(f"\n总计采集 {len(all_jobs)} 条，去重后 {len(unique_jobs)} 条")

    # 追加到 raw_jobs.json（先读取已有内容）
    raw_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw_jobs.json")
    existing: list[dict] = []
    if os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing.extend(unique_jobs)

    # 再次去重
    seen2: set[tuple[str, str]] = set()
    final_jobs: list[dict] = []
    for job in existing:
        key = (job.get("title", ""), job.get("company_name", job.get("company", "")))
        if key not in seen2:
            seen2.add(key)
            final_jobs.append(job)

    save_jobs(final_jobs, raw_path)
    print(f"已保存 {len(final_jobs)} 条到 raw_jobs.json")


if __name__ == "__main__":
    asyncio.run(main())
