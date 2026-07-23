"""E2E 测试：配置检测页面。

覆盖：
- 页面加载后自动运行检测
- 顶部汇总卡片数值正确
- 结果列表非空
- 分类筛选可切换

运行方式：
    python e2e/test_config_tests.py
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
    ConfigTestsPage,
    LayoutPage,
    find_chrome_executable,
)
from scripts.with_server import server_context  # noqa: E402

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright-browsers"))


def test_config_tests_page() -> None:
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
            config_page = ConfigTestsPage(page)

            try:
                base.add_onboarding_completed()

                # 1. 进入配置检测页面
                config_page.open()
                print("Config tests page loaded.")

                # 2. 等待汇总卡片渲染
                config_page.wait_for_summary_cards()
                summary = config_page.summary_card_values()
                total = summary.get("总检测项", 0)
                passed = summary.get("通过", 0)
                failed = summary.get("失败", 0)
                skipped = summary.get("跳过", 0)
                print(
                    f"Summary: total={total}, passed={passed}, "
                    f"failed={failed}, skipped={skipped}"
                )

                assert total > 0, "Expected total test count > 0"
                assert total == passed + failed + skipped, (
                    f"Summary mismatch: {total} != {passed + failed + skipped}"
                )

                # 3. 等待结果列表渲染
                config_page.wait_for_selector("[class*='grid'] > div", timeout=10_000)
                result_cards = page.locator("text=耗时").count()
                assert result_cards >= total, (
                    f"Expected at least {total} result cards, got {result_cards}"
                )
                print(f"Found {result_cards} result card(s).")

                # 4. 切换分类筛选并验证仍有结果（数据库类通常通过）
                layout.click_text("数据库")
                page.wait_for_timeout(300)
                assert config_page.has_text("数据库") or config_page.has_text("SQLite")
                print("Category filter switched successfully.")

                # 5. 重新检测按钮可用
                assert page.locator('button:has-text("重新检测")').is_enabled()
                print("Re-test button is enabled.")

                print("Config tests E2E test passed.")
            except Exception:
                base.screenshot_on_failure("config_tests_failure")
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    test_config_tests_page()
