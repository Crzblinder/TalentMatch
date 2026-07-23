"""E2E 测试：岗位收藏功能。

覆盖：
- 在岗位库收藏指定岗位
- 进入我的收藏页面，验证该岗位出现
- 验证导航高亮为"我的收藏"而非"岗位库"

运行方式：
    python e2e/test_favorites.py
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
    LayoutPage,
    find_chrome_executable,
)
from scripts.with_server import server_context  # noqa: E402

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright-browsers"))


def test_favorites_flow() -> None:
    chrome = find_chrome_executable()
    if chrome is None:
        raise FileNotFoundError(
            "Playwright Chromium not found. "
            "Set PLAYWRIGHT_BROWSERS_PATH and run 'playwright install chromium'."
        )

    print(f"Using Chromium: {chrome}")

    target_job = "Python 后端工程师"

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

            try:
                base.add_onboarding_completed()

                # 1. 进入岗位库并等待画像加载完成
                job_library.open()
                page.wait_for_selector("text=当前画像：", timeout=10_000)
                job_library.wait_for_text("示例候选人", timeout=10_000)
                print("Job library loaded with profile.")

                # 2. 搜索并收藏目标岗位
                job_library.search_job(target_job)
                job_library.wait_for_text(target_job, timeout=10_000)
                job_library.toggle_favorite(target_job)
                job_library.wait_for_favorite_state(target_job, active=True)
                assert job_library.is_favorite_active(target_job), (
                    f"Expected {target_job} to be favorited"
                )
                print(f"Favorited job: {target_job}")

                # 3. 通过导航进入我的收藏
                layout.navigate_to("我的收藏")
                job_library.wait_for_text("我的收藏")
                assert layout.is_nav_active("我的收藏")
                assert not layout.is_nav_active("岗位库")
                base.assert_exactly_one_active_nav()
                print("Favorites page is active and nav is highlighted correctly.")

                # 4. 验证收藏列表包含目标岗位
                job_library.wait_for_text(target_job, timeout=10_000)
                assert job_library.has_text(target_job), (
                    f"Expected favorites list to contain {target_job}"
                )
                rows = job_library.job_rows()
                assert rows >= 1, "Expected at least one favorite row"
                print(f"Favorites list contains {rows} row(s), including {target_job}.")

                # 5. 取消收藏，验证从收藏列表移除
                job_library.toggle_favorite(target_job)
                page.wait_for_timeout(500)
                assert not job_library.has_text(target_job), (
                    f"Expected {target_job} to be removed from favorites"
                )
                print("Unfavorited job successfully.")

                print("Favorites E2E test passed.")
            except Exception:
                base.screenshot_on_failure("favorites_failure")
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    test_favorites_flow()
