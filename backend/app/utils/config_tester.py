"""外部配置可用性检测工具。

提供一组轻量级探测函数，用于验证 TalentMatch 引入的各类外部服务
（LLM、搜索、文档解析、招聘平台抓取、内容安全等）是否可用。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import requests

from app.config import Settings


@dataclass
class ConfigTestResult:
    """单个配置项的检测结果。"""

    name: str
    category: str
    status: str  # ok | fail | skip
    message: str
    response_time_ms: float = 0.0
    configured: bool = False
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigTestReport:
    """完整检测报告。"""

    tested_at: str
    total: int
    passed: int
    failed: int
    skipped: int
    results: list[ConfigTestResult]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_test(
    name: str,
    category: str,
    configured: bool,
    test_fn: callable,
) -> ConfigTestResult:
    """包装单个测试：记录耗时、捕获异常、统一返回格式。"""
    if not configured:
        return ConfigTestResult(
            name=name,
            category=category,
            status="skip",
            message="未配置相关参数，已跳过",
            configured=False,
        )

    start = time.perf_counter()
    try:
        message, detail = test_fn()
        status = "ok"
    except Exception as exc:  # noqa: BLE001
        message = f"检测失败: {exc}"
        detail = {}
        status = "fail"
    elapsed = (time.perf_counter() - start) * 1000

    return ConfigTestResult(
        name=name,
        category=category,
        status=status,
        message=message,
        response_time_ms=round(elapsed, 2),
        configured=True,
        detail=detail,
    )


def _test_database(settings: Settings) -> ConfigTestResult:
    configured = bool(settings.effective_database_url)

    def _check() -> tuple[str, dict[str, Any]]:
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.effective_database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()
        url_type = "mysql" if "mysql" in settings.effective_database_url.lower() else "sqlite"
        return "数据库连接正常", {"url_type": url_type}

    return _run_test("数据库", "database", configured, _check)


def _test_vector_db(settings: Settings) -> ConfigTestResult:
    configured = bool(settings.vector_db_path)

    def _check() -> tuple[str, dict[str, Any]]:
        import chromadb

        client = chromadb.PersistentClient(path=settings.vector_db_path)
        client.heartbeat()
        return "向量数据库连接正常", {"path": settings.vector_db_path}

    return _run_test("向量数据库 (Chroma)", "vector", configured, _check)


def _test_ollama(settings: Settings) -> ConfigTestResult:
    configured = settings.use_local_llm and bool(settings.ollama_base_url)

    def _check() -> tuple[str, dict[str, Any]]:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        models = r.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        target = settings.ollama_model
        if target not in model_names and f"{target}:latest" not in model_names:
            return f"服务正常，但未找到模型 {target}", {"available_models": model_names[:10]}
        return f"Ollama 服务正常，模型 {target} 可用", {"available_models": model_names[:10]}

    return _run_test("Ollama 本地 LLM", "llm", configured, _check)


def _test_openai(settings: Settings) -> ConfigTestResult:
    configured = (
        bool(settings.openai_api_key)
        and not settings.use_local_llm
        and not settings.use_domestic_llm
    )

    def _check() -> tuple[str, dict[str, Any]]:
        r = requests.get(
            f"{settings.openai_base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            timeout=15,
        )
        r.raise_for_status()
        return f"OpenAI API 可访问，模型 {settings.openai_model}", {}

    return _run_test("OpenAI / 兼容 API", "llm", configured, _check)


def _test_dashscope(settings: Settings) -> ConfigTestResult:
    configured = settings.use_domestic_llm and bool(settings.dashscope_api_key)

    def _check() -> tuple[str, dict[str, Any]]:
        r = requests.get(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
            headers={"Authorization": f"Bearer {settings.dashscope_api_key}"},
            timeout=15,
        )
        r.raise_for_status()
        return f"阿里云百炼 API 可访问，模型 {settings.dashscope_model}", {}

    return _run_test("阿里云百炼 DashScope", "llm", configured, _check)


def _test_zhipu(settings: Settings) -> ConfigTestResult:
    configured = settings.use_domestic_llm and bool(settings.zhipu_api_key)

    def _check() -> tuple[str, dict[str, Any]]:
        r = requests.post(
            f"{settings.zhipu_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.zhipu_api_key}"},
            json={
                "model": settings.zhipu_model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5,
            },
            timeout=20,
        )
        r.raise_for_status()
        return f"智谱 AI API 可访问，模型 {settings.zhipu_model}", {}

    return _run_test("智谱 AI", "llm", configured, _check)


def _test_bocha(settings: Settings) -> ConfigTestResult:
    configured = bool(settings.bocha_api_key)

    def _check() -> tuple[str, dict[str, Any]]:
        r = requests.post(
            "https://api.bochaai.com/v1/web-search",
            headers={
                "Authorization": f"Bearer {settings.bocha_api_key}",
                "Content-Type": "application/json",
            },
            json={"query": "Python 后端", "count": 1},
            timeout=20,
        )
        r.raise_for_status()
        return "博查搜索 API 可访问", {}

    return _run_test("博查 Bocha 搜索", "search", configured, _check)


def _test_searxng(settings: Settings) -> ConfigTestResult:
    configured = bool(settings.searxng_base_url)

    def _check() -> tuple[str, dict[str, Any]]:
        url = f"{settings.searxng_base_url.rstrip('/')}/search"
        r = requests.get(url, params={"q": "Python", "format": "json"}, timeout=15)
        r.raise_for_status()
        results = r.json().get("results", [])
        return f"SearXNG 可访问，返回 {len(results)} 条结果", {"result_count": len(results)}

    return _run_test("SearXNG 本地搜索", "search", configured, _check)


def _test_tavily(settings: Settings) -> ConfigTestResult:
    configured = bool(settings.tavily_api_key)

    def _check() -> tuple[str, dict[str, Any]]:
        r = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={"api_key": settings.tavily_api_key, "query": "Python backend", "max_results": 1},
            timeout=20,
        )
        r.raise_for_status()
        return "Tavily 搜索 API 可访问", {}

    return _run_test("Tavily 搜索", "search", configured, _check)


def _test_duckduckgo(settings: Settings) -> ConfigTestResult:
    configured = True  # 无需配置，默认兜底

    def _check() -> tuple[str, dict[str, Any]]:
        try:
            from duckduckgo_search import DDGS

            with DDGS(timeout=10) as ddgs:
                results = list(ddgs.text("Python backend", max_results=1))
            return (
                f"DuckDuckGo 搜索可用，返回 {len(results)} 条结果",
                {"result_count": len(results)},
            )
        except Exception as exc:  # noqa: BLE001
            raise Exception(f"DuckDuckGo 不可用: {exc}") from exc

    return _run_test("DuckDuckGo 搜索", "search", configured, _check)


def _test_dashscope_doc_parse(settings: Settings) -> ConfigTestResult:
    configured = bool(settings.dashscope_api_key) and bool(settings.dashscope_doc_parse_model)

    def _check() -> tuple[str, dict[str, Any]]:
        r = requests.get(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
            headers={"Authorization": f"Bearer {settings.dashscope_api_key}"},
            timeout=15,
        )
        r.raise_for_status()
        return f"百炼文档解析配置就绪，模型 {settings.dashscope_doc_parse_model}", {}

    return _run_test("百炼文档解析", "parse", configured, _check)


def _test_domestic_crawler(settings: Settings) -> ConfigTestResult:
    configured = settings.domestic_crawler_enabled

    def _check() -> tuple[str, dict[str, Any]]:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            return "Playwright 已安装，国内招聘平台抓取可用", {}
        except Exception as exc:  # noqa: BLE001
            return f"Playwright 未就绪: {exc}", {}

    return _run_test("国内招聘平台抓取", "crawler", configured, _check)


def _test_content_safety(settings: Settings) -> ConfigTestResult:
    configured = settings.enable_content_safety and bool(settings.alibaba_cloud_access_key_id)

    def _check() -> tuple[str, dict[str, Any]]:
        from app.utils.content_safety import check_text_safety

        result = check_text_safety("测试文本", settings)
        return f"阿里云内容安全接口可调用，结果: {result.get('suggestion', 'unknown')}", result

    return _run_test("阿里云内容安全", "safety", configured, _check)


def _test_resume_masking(settings: Settings) -> ConfigTestResult:
    configured = True  # 总开关可检测

    def _check() -> tuple[str, dict[str, Any]]:
        from app.utils.content_safety import mask_sensitive_text

        masked = mask_sensitive_text("手机号 13800138000，身份证 110101199001011234")
        status = "开启" if settings.enable_resume_masking else "关闭"
        return f"简历脱敏功能正常，状态: {status}", {"sample": masked}

    return _run_test("简历数据脱敏", "safety", configured, _check)


def run_config_tests(settings: Settings | None = None) -> ConfigTestReport:
    """运行全部配置可用性检测并返回报告。"""
    if settings is None:
        from app.config import get_settings

        settings = get_settings()

    testers = [
        _test_database,
        _test_vector_db,
        _test_ollama,
        _test_openai,
        _test_dashscope,
        _test_zhipu,
        _test_bocha,
        _test_searxng,
        _test_tavily,
        _test_duckduckgo,
        _test_dashscope_doc_parse,
        _test_domestic_crawler,
        _test_content_safety,
        _test_resume_masking,
    ]

    results: list[ConfigTestResult] = []
    for tester in testers:
        try:
            results.append(tester(settings))
        except Exception as exc:  # noqa: BLE001
            results.append(
                ConfigTestResult(
                    name=tester.__name__.replace("_test_", ""),
                    category="unknown",
                    status="fail",
                    message=f"测试执行异常: {exc}",
                )
            )

    passed = sum(1 for r in results if r.status == "ok")
    failed = sum(1 for r in results if r.status == "fail")
    skipped = sum(1 for r in results if r.status == "skip")

    return ConfigTestReport(
        tested_at=_now_iso(),
        total=len(results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        results=results,
    )
