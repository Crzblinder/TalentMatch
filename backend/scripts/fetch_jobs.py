"""手动触发真实 JD 爬虫并保存到 backend/data/raw_jobs.json。"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.crawler.scraper import JobScraper, save_jobs

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    scraper = JobScraper()
    jobs = asyncio.run(scraper.fetch_all())
    path = save_jobs(jobs)
    print(f"采集到 {len(jobs)} 条真实 JD，已保存至 {path}")


if __name__ == "__main__":
    main()
