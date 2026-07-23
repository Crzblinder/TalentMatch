"""端到端冒烟测试：验证新版岗位技能匹配核心用户旅程。

覆盖页面：
- 仪表盘（/）
- 岗位库（/jobs）
- 我的收藏（/favorites）
- 技能图谱（/skills）
- 趋势分析（/trends）
- 岗位匹配（/match）

运行方式：
    cd /workspace
    python e2e/test_job_match_flow.py

依赖：Playwright Chromium（首次运行需要 python -m playwright install chromium）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from e2e.pages import (  # noqa: E402
    BasePage,
    JobLibraryPage,
    JobMatchPage,
    LayoutPage,
    find_chrome_executable,
)
from scripts.with_server import server_context  # noqa: E402

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright-browsers"))


def test_job_match_flow() -> None:
    chrome = find_chrome_executable()
    if chrome is None:
        raise FileNotFoundError(
            "Playwright Chromium not found. "
            "Set PLAYWRIGHT_BROWSERS_PATH and run 'playwright install chromium'."
        )

    print(f"Using Chromium: {chrome}")

    with server_context():
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=str(chrome),
            )
            page = browser.new_page()
            base = BasePage(page)
            layout = LayoutPage(page)
            job_library = JobLibraryPage(page)
            job_match = JobMatchPage(page)

            try:
                # 预先标记新手引导已完成，避免首页弹窗阻塞后续断言
                base.add_onboarding_completed()

                # 1. 仪表盘
                base.goto("/")
                assert base.has_text("TalentMatch Engine")
                base.wait_for_selector("h2", timeout=10_000)
                print("Dashboard loaded.")

                # 2. 岗位库
                layout.navigate_to("岗位库")
                job_library.wait_for_selector("table tbody tr")
                rows = job_library.job_rows()
                assert rows > 0, "Expected jobs to be listed"
                print(f"Job library loaded with {rows} rows.")

                # 3. 我的收藏（独立路由，不应与岗位库同时高亮）
                layout.navigate_to("我的收藏")
                job_library.wait_for_text("我的收藏")
                base.assert_exactly_one_active_nav()
                print("Favorites page loaded with single active nav item.")

                # 4. 技能图谱
                layout.navigate_to("技能图谱")
                base.wait_for_text("技能知识图谱")
                print("Skill graph page loaded.")

                # 5. 趋势分析
                layout.navigate_to("趋势分析")
                base.wait_for_text("岗位趋势分析")
                print("Trend analysis page loaded.")

                # 6. 岗位匹配
                layout.navigate_to("岗位匹配")
                job_match.run_full_match("E2E 测试候选人", "Python, FastAPI")
                print("Match completed successfully.")

                print("E2E smoke test passed.")
            except Exception:
                base.screenshot_on_failure("failure")
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    test_job_match_flow()
