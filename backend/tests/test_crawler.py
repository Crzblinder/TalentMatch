"""JD 爬虫解析逻辑单元测试。"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from bs4 import BeautifulSoup

from app.crawler.scraper import (
    JobScraper,
    _extract_city,
    _extract_company,
    _extract_education,
    _extract_experience,
    _extract_salary,
    _extract_skills,
    _is_job_related,
    _parse_boss_job,
    _parse_zhilian_job,
    scrape_domestic_jobs,
)
from app.data.generator import get_skill_pool


@pytest.mark.parametrize(
    "text,expected",
    [
        ("招聘 Java 后端，15k-25k", (15000, 25000)),
        ("薪资 20K-30K，本科", (20000, 30000)),
        ("月薪 15000-25000 元", (15000, 25000)),
        ("待遇 30k+", (None, None)),
        ("无薪资信息", (None, None)),
    ],
)
def test_extract_salary(text, expected):
    assert _extract_salary(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("要求 3-5 年经验", "3-5年"),
        ("1-3 年相关经验", "1-3年"),
        ("应届生优先", "应届/在校生"),
        ("10年以上经验", "10年以上"),
        ("不限经验", ""),
    ],
)
def test_extract_experience(text, expected):
    assert _extract_experience(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("本科及以上学历", "本科"),
        ("硕士优先", "硕士"),
        ("大专即可", "大专"),
        ("博士学历", "博士"),
        ("无学历要求", ""),
    ],
)
def test_extract_education(text, expected):
    assert _extract_education(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("[北京] 招聘 Java", "北京"),
        ("上海/杭州 两地办公", "上海/杭州"),
        ("Remote", ""),
    ],
)
def test_extract_city(text, expected):
    assert _extract_city(text) == expected


@pytest.mark.parametrize(
    "title,content,expected",
    [
        ("[某科技公司] 招聘", "", "某科技公司"),
        ("招聘", "公司：ABC 科技", "ABC 科技"),
        ("", "未来智能有限公司", "未来智能"),
    ],
)
def test_extract_company(title, content, expected):
    assert _extract_company(title, content) == expected


def test_extract_skills():
    text = "熟悉 Python、FastAPI 和 PostgreSQL，了解 Docker"
    skills = _extract_skills(text, get_skill_pool())
    assert "Python" in skills
    assert "FastAPI" in skills
    assert "PostgreSQL" in skills
    assert "Docker" in skills


def test_is_job_related():
    assert _is_job_related("[北京] 招聘 Java 后端", "") is True
    assert _is_job_related("公司年会通知", "") is False


def test_scraper_parse_job():
    scraper = JobScraper()
    entry = {
        "title": "[上海] 高级 Python 后端工程师 25k-40k",
        "content": (
            "负责后端系统开发，要求 3-5 年经验，本科及以上学历，"
            "熟悉 Python、FastAPI、PostgreSQL、Docker。"
        ),
        "link": "https://example.com/job/1",
        "published_at": "2024-01-01T00:00:00Z",
    }
    job = scraper._parse_job(entry, "test_source")
    assert job["title"] == "[上海] 高级 Python 后端工程师 25k-40k"
    assert job["city"] == "上海"
    assert job["salary_min"] == 25000
    assert job["salary_max"] == 40000
    assert job["experience_level"] == "3-5年"
    assert job["education_level"] == "本科"
    assert "Python" in job["required_skills"]
    assert "Docker" in job["required_skills"]


BOSS_CARD_HTML = """
<div class="job-card-wrapper">
  <a href="/job_detail/123.html" class="job-name">高级 Python 后端工程师</a>
  <div class="company-name">示例科技</div>
  <div class="salary">25k-40k</div>
  <div class="job-area">北京·朝阳区</div>
</div>
"""

ZHILIAN_CARD_HTML = """
<div class="joblist-item">
  <a class="jobinfo__name" href="/jobs/456.html">Python 开发工程师</a>
  <div class="company__name">未来网络</div>
  <div class="jobinfo__salary">15k-25k</div>
  <div class="jobinfo__area">上海</div>
</div>
"""


def _soup_tag(html: str) -> Any:
    return BeautifulSoup(html, "html.parser").find("div")


def test_parse_boss_job():
    tag = _soup_tag(BOSS_CARD_HTML)
    job = _parse_boss_job(tag)
    assert job["title"] == "高级 Python 后端工程师"
    assert job["company"] == "示例科技"
    assert job["salary"] == "25k-40k"
    assert "北京" in job["location"]
    assert job["url"] == "https://www.zhipin.com/job_detail/123.html"
    assert "Python" in job["description"]
    assert "示例科技" in job["description"]


def test_parse_zhilian_job():
    tag = _soup_tag(ZHILIAN_CARD_HTML)
    job = _parse_zhilian_job(tag)
    assert job["title"] == "Python 开发工程师"
    assert job["company"] == "未来网络"
    assert job["salary"] == "15k-25k"
    assert "上海" in job["location"]
    assert job["url"] == "https://www.zhaopin.com/jobs/456.html"
    assert "Python" in job["description"]


def test_convert_domestic_job():
    scraper = JobScraper()
    raw = {
        "title": "高级 Python 后端工程师",
        "company": "示例科技",
        "location": "北京·朝阳区",
        "salary": "25k-40k",
        "url": "https://www.zhipin.com/job_detail/123.html",
        "description": "高级 Python 后端工程师 | 示例科技 | 25k-40k | 北京·朝阳区",
        "published_at": "",
    }
    job = scraper._convert_domestic_job(raw, "boss_zhipin")
    assert job["title"] == "高级 Python 后端工程师"
    assert job["company_name"] == "示例科技"
    assert job["city"] == "北京"
    assert job["salary_min"] == 25000
    assert job["salary_max"] == 40000
    assert "Python" in job["required_skills"]
    assert job["source"] == "boss_zhipin"
    assert job["source_url"] == "https://www.zhipin.com/job_detail/123.html"


def _make_disabled_settings() -> Any:
    class _Settings:
        domestic_crawler_enabled = False
        playwright_headless = True
        domestic_crawler_delay_ms = 1000

    return _Settings()


def _make_enabled_settings() -> Any:
    class _Settings:
        domestic_crawler_enabled = True
        playwright_headless = True
        domestic_crawler_delay_ms = 1000

    return _Settings()


@pytest.fixture
def boss_source() -> dict[str, Any]:
    return {
        "name": "boss_zhipin",
        "type": "domestic_web",
        "platform": "boss",
        "enabled": False,
        "base_url": "https://www.zhipin.com",
        "search_url_template": "https://www.zhipin.com/web/geek/job?query={keyword}&city={city}",
        "city_code": "101010100",
        "keyword": "Python",
        "job_selector": [".job-card-wrapper"],
    }


def test_fetch_domestic_web_disabled(boss_source: dict[str, Any], monkeypatch: Any) -> None:
    """源或总开关关闭时不应发起真实请求。"""
    monkeypatch.setattr(
        "app.crawler.scraper.get_settings", lambda: _make_disabled_settings()
    )
    called = {"times": 0}

    def fake_sync(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        called["times"] += 1
        return []

    monkeypatch.setattr("app.crawler.scraper._fetch_domestic_web_sync", fake_sync)
    result = asyncio.run(JobScraper()._fetch_domestic_web(boss_source))
    assert result == []
    assert called["times"] == 0


def test_fetch_domestic_web_failure_returns_empty(
    boss_source: dict[str, Any], monkeypatch: Any
) -> None:
    """抓取失败时应返回空列表且不抛出异常。"""
    boss_source["enabled"] = True
    monkeypatch.setattr(
        "app.crawler.scraper.get_settings", lambda: _make_enabled_settings()
    )

    def fake_sync_raise(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        raise RuntimeError("模拟页面超时")

    monkeypatch.setattr("app.crawler.scraper._fetch_domestic_web_sync", fake_sync_raise)
    result = asyncio.run(JobScraper()._fetch_domestic_web(boss_source))
    assert result == []


def test_scrape_domestic_jobs_disabled(monkeypatch: Any) -> None:
    """总开关关闭时 scrape_domestic_jobs 直接返回空列表。"""
    monkeypatch.setattr(
        "app.crawler.scraper.get_settings", lambda: _make_disabled_settings()
    )
    result = asyncio.run(scrape_domestic_jobs("Python", "北京"))
    assert result == []
