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

# 使 scripts.with_server 可被导入
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.with_server import server_context

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright-browsers"))


def find_chrome_executable() -> Path | None:
    """Locate the Chromium binary downloaded by Playwright."""
    search_paths: list[Path] = []
    env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env_path:
        search_paths.append(Path(env_path))
    if sys.platform == "win32":
        search_paths.append(Path.home() / "AppData" / "Local" / "ms-playwright")
    else:
        search_paths.append(Path.home() / ".cache" / "ms-playwright")

    for browsers_path in search_paths:
        if sys.platform == "win32":
            candidates = list(browsers_path.rglob("chrome.exe"))
        else:
            candidates = [p for p in browsers_path.rglob("chrome") if p.is_file()]
        if candidates:
            return candidates[0]
    return None


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
            page.set_default_timeout(30_000)

            try:
                # 预先标记新手引导已完成，避免首页弹窗阻塞后续断言
                page.add_init_script("localStorage.setItem('onboarding_completed', 'true');")

                # 1. 仪表盘
                page.goto("http://127.0.0.1:5173/")
                page.wait_for_load_state("networkidle")
                assert "TalentMatch Engine" in page.content()
                page.locator("h2", has_text="技能图谱仪表盘").wait_for()
                print("Dashboard loaded.")

                # 2. 岗位库
                page.click("text=岗位库")
                page.wait_for_selector("text=岗位库")
                page.wait_for_selector("table tbody tr")
                rows = page.locator("table tbody tr").count()
                assert rows > 0, "Expected jobs to be listed"
                print(f"Job library loaded with {rows} rows.")

                # 3. 我的收藏（独立路由，不应与岗位库同时高亮）
                page.click("text=我的收藏")
                page.wait_for_selector("text=我的收藏")
                active_links = page.locator("nav a[class*='bg-primary']").count()
                assert active_links == 1, f"Expected exactly one active nav item, got {active_links}"
                print("Favorites page loaded with single active nav item.")

                # 4. 技能图谱
                page.click("text=技能图谱")
                page.wait_for_selector("text=技能知识图谱")
                print("Skill graph page loaded.")

                # 5. 趋势分析
                page.click("text=趋势分析")
                page.wait_for_selector("text=岗位趋势分析")
                print("Trend analysis page loaded.")

                # 6. 岗位匹配
                page.click("text=岗位匹配")
                page.wait_for_selector("text=岗位技能匹配")

                # 填写画像：新版多 Tab 表单
                page.fill('input[placeholder="请输入姓名"]', "E2E 测试候选人")

                # 跳转到技能优势 Tab 填写技能
                page.click("text=技能优势")
                page.fill(
                    'textarea[placeholder="输入技能，用逗号分隔，例如：Python, MySQL, 数据分析"]',
                    "Python, FastAPI",
                )

                # 进入下一步
                page.click('button:has-text("下一步")')
                page.wait_for_selector("text=选择目标岗位")

                # 选择第一个岗位
                page.locator("table tbody tr").first.click()
                print("Selected a target job.")

                # 开始匹配
                page.click('button:has-text("开始匹配")')
                page.wait_for_selector("text=匹配结果", timeout=45_000)
                print("Match completed successfully.")

                print("E2E smoke test passed.")
            except Exception:
                page.screenshot(path=str(ROOT / "e2e" / "failure.png"))
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    test_job_match_flow()
