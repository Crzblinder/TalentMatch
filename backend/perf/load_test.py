#!/usr/bin/env python3
"""本地负载测试脚本：并发解析与匹配基准。

默认测试本机已启动的后端服务（http://127.0.0.1:8000）。
测试前请确保已运行 `python scripts/start.py` 或单独启动后端。

运行方式：
    cd backend
    python -m perf.load_test

环境变量：
    BASE_URL: 后端地址，默认 http://127.0.0.1:8000
    CONCURRENCY: 并发数，默认 5
    REQUESTS: 每个场景总请求数，默认 20
"""

from __future__ import annotations

import os
import statistics
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
CONCURRENCY = int(os.environ.get("CONCURRENCY", "5"))
REQUESTS = int(os.environ.get("REQUESTS", "20"))

JD_TEXT = """某科技公司招聘 Python 后端工程师
岗位职责：负责后端服务开发。
岗位要求：熟悉 Python、FastAPI、PostgreSQL，3-5 年经验，本科及以上学历。"""

RESUME_TEXT = """张三
手机：13812345678
邮箱：zhangsan@example.com

教育经历
2016.09-2020.06 北京大学 计算机科学与技术 本科

工作经历
2020.07-2023.03 某科技有限公司 Python后端工程师
负责后端服务开发，使用 Python、FastAPI 和 PostgreSQL。

技能
Python、FastAPI、PostgreSQL、Docker

求职意向
期望岗位：Python后端工程师
"""


def _api(path: str) -> str:
    return f"{BASE_URL}/api/v1{path}"


def _check_health() -> None:
    try:
        resp = requests.get(_api("/jobs/health"), timeout=5)
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"后端 {BASE_URL} 无法访问，请先启动服务。错误：{exc}"
        ) from exc


def _setup_match_fixture() -> tuple[int, int]:
    """创建测试画像并返回第一个岗位的 ID。"""
    profile_payload = {
        "name": "LoadTestProfile",
        "skills": ["Python", "FastAPI", "Docker"],
        "experience_level": "3-5年",
        "target_job_titles": ["Python 后端工程师"],
        "is_active": True,
    }
    profile_resp = requests.post(_api("/profiles"), json=profile_payload, timeout=10)
    profile_resp.raise_for_status()
    profile_id = profile_resp.json()["data"]["id"]

    jobs_resp = requests.get(_api("/jobs"), params={"size": 1}, timeout=10)
    jobs_resp.raise_for_status()
    jobs = jobs_resp.json()["data"]["items"]
    if not jobs:
        raise RuntimeError("岗位库为空，请先注入种子数据")
    job_id = jobs[0]["id"]
    return profile_id, job_id


def _run_scenario(
    name: str,
    func: Callable[[], requests.Response],
    concurrency: int = CONCURRENCY,
    total_requests: int = REQUESTS,
) -> dict[str, float | int]:
    """执行并发场景并返回统计信息。"""
    latencies: list[float] = []
    success = 0
    failure = 0
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(func) for _ in range(total_requests)]
        for future in as_completed(futures):
            try:
                resp = future.result()
                latencies.append(resp.elapsed.total_seconds())
                if resp.status_code == 200:
                    success += 1
                else:
                    failure += 1
            except Exception:
                failure += 1

    elapsed = time.perf_counter() - start
    count = success + failure
    return {
        "name": name,
        "total": count,
        "success": success,
        "failure": failure,
        "rps": round(count / elapsed, 2) if elapsed > 0 else 0.0,
        "avg_latency_ms": round(statistics.mean(latencies) * 1000, 2) if latencies else 0.0,
        "p95_latency_ms": round(
            statistics.quantiles(latencies, n=20)[18] * 1000, 2
        ) if len(latencies) >= 20 else round(max(latencies) * 1000, 2) if latencies else 0.0,
        "max_latency_ms": round(max(latencies) * 1000, 2) if latencies else 0.0,
    }


def _print_report(results: list[dict[str, float | int]]) -> None:
    print("\nTalentMatch 负载测试报告")
    print("=" * 80)
    print(
        f"{'场景':<20} {'总请求':>8} {'成功':>8} {'失败':>8} "
        f"{'RPS':>8} {'平均(ms)':>10} {'P95(ms)':>10} {'最大(ms)':>10}"
    )
    print("-" * 80)
    for r in results:
        print(
            f"{r['name']:<20} {r['total']:>8} {r['success']:>8} {r['failure']:>8} "
            f"{r['rps']:>8.2f} {r['avg_latency_ms']:>10.2f} "
            f"{r['p95_latency_ms']:>10.2f} {r['max_latency_ms']:>10.2f}"
        )
    print("=" * 80)


def main() -> int:
    _check_health()
    print(f"后端健康检查通过：{BASE_URL}")

    profile_id, job_id = _setup_match_fixture()
    print(f"测试夹具就绪：profile_id={profile_id}, job_id={job_id}")

    scenarios = [
        (
            "JD 解析",
            lambda: requests.post(
                _api("/jobs/parse"),
                json={"jd_text": JD_TEXT},
                timeout=30,
            ),
        ),
        (
            "简历解析",
            lambda: requests.post(
                _api("/resumes/parse"),
                json={"resume_text": RESUME_TEXT},
                timeout=30,
            ),
        ),
        (
            "岗位匹配",
            lambda: requests.post(
                _api("/matches"),
                json={"profile_id": profile_id, "job_id": job_id},
                timeout=30,
            ),
        ),
    ]

    results: list[dict[str, float | int]] = []
    for name, func in scenarios:
        print(f"\n开始场景：{name}（并发={CONCURRENCY}, 请求数={REQUESTS}）...")
        results.append(_run_scenario(name, func))

    _print_report(results)

    total_failures = sum(r["failure"] for r in results)
    if total_failures > 0:
        print(f"\n存在 {total_failures} 个失败请求，请检查后端日志。")
        return 1
    print("\n所有场景均完成且无失败。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
