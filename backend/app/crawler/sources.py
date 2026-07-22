"""真实岗位数据源配置。

每个源定义包含：
- name: 数据源名称
- type: 采集类型 (rss / seed / domestic_web)
- url: 公开 RSS 地址（rss 类型）
- parser: 解析方式 (rss_atom)（rss 类型）
- description: 数据源说明
- requires_filter: 是否需要从通用内容中过滤出招聘帖

国内平台源（domestic_web）默认关闭，避免开发/测试环境误触发反爬。
"""

from typing import Any

SOURCES: list[dict[str, Any]] = [
    {
        "name": "v2ex_jobs",
        "type": "rss",
        "url": "https://www.v2ex.com/feed/jobs.xml",
        "parser": "rss_atom",
        "description": "V2EX 酷工作节点 RSS，中文技术岗位公开源",
        "requires_filter": False,
    },
    {
        "name": "ruby_china_jobs",
        "type": "rss",
        "url": "https://ruby-china.org/topics/feed",
        "parser": "rss_atom",
        "description": "Ruby China 社区话题 RSS，偶含技术岗位",
        "requires_filter": True,
    },
    {
        "name": "learnku_python_jobs",
        "type": "rss",
        "url": "https://learnku.com/python/feed",
        "parser": "rss_atom",
        "description": "LearnKu Python 社区 RSS，含招聘/求职帖",
        "requires_filter": True,
    },
    {
        "name": "learnku_laravel_jobs",
        "type": "rss",
        "url": "https://learnku.com/laravel/feed",
        "parser": "rss_atom",
        "description": "LearnKu Laravel 社区 RSS，含 PHP/前端岗位帖",
        "requires_filter": True,
    },
    {
        "name": "learnku_go_jobs",
        "type": "rss",
        "url": "https://learnku.com/go/feed",
        "parser": "rss_atom",
        "description": "LearnKu Go 社区 RSS，含 Go 岗位帖",
        "requires_filter": True,
    },
    # -----------------------------------------------------------------------
    # 国内招聘平台公开列表页（默认关闭，需同时开启配置 DOMESTIC_CRAWLER_ENABLED）
    # -----------------------------------------------------------------------
    {
        "name": "boss_zhipin",
        "type": "domestic_web",
        "platform": "boss",
        "enabled": False,
        "base_url": "https://www.zhipin.com",
        "search_url_template": "https://www.zhipin.com/web/geek/job?query={keyword}&city={city}",
        "city_code": "101010100",  # 北京
        "keyword": "Python",
        "job_selector": [".job-card-wrapper", ".job-card-pc", "li.job-card-pc"],
        "description": "Boss 直聘公开列表页（Playwright 抓取）",
    },
    {
        "name": "zhilian_zhaopin",
        "type": "domestic_web",
        "platform": "zhilian",
        "enabled": False,
        "base_url": "https://www.zhaopin.com",
        "search_url_template": "https://sou.zhaopin.com/?jl={city}&kw={keyword}",
        "city_code": "530",  # 北京
        "keyword": "Python",
        "job_selector": [".joblist-item", ".positionlist-item", "[class*='joblist-item']"],
        "description": "智联招聘公开列表页（Playwright 抓取）",
    },
]
