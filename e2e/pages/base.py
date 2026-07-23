"""E2E 测试 Page Object 基类与通用工具。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import Page

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

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


class BasePage:
    """Page Object 基类，封装常用 Playwright 操作。"""

    def __init__(self, page: Page, root_url: str = "http://127.0.0.1:5173") -> None:
        self.page = page
        self.root_url = root_url
        self.page.set_default_timeout(30_000)

    def goto(self, path: str = "/") -> None:
        """导航到指定前端路径。"""
        self.page.goto(f"{self.root_url}{path}")
        self.page.wait_for_load_state("networkidle")

    def screenshot_on_failure(self, name: str) -> None:
        """失败时保存截图到 e2e/ 目录。"""
        self.page.screenshot(path=str(ROOT / "e2e" / f"{name}.png"))

    def fill_text(self, selector: str, text: str) -> None:
        """填充文本输入框。"""
        self.page.fill(selector, text)

    def click(self, selector: str) -> None:
        """点击元素。"""
        self.page.click(selector)

    def click_text(self, text: str) -> None:
        """根据文本内容点击。"""
        self.page.click(f"text={text}")

    def wait_for_text(self, text: str, timeout: int = 30_000) -> None:
        """等待指定文本出现在页面上。"""
        self.page.wait_for_selector(f"text={text}", timeout=timeout)

    def wait_for_selector(self, selector: str, timeout: int = 30_000) -> None:
        """等待选择器匹配的元素出现。"""
        self.page.wait_for_selector(selector, timeout=timeout)

    def has_text(self, text: str) -> bool:
        """判断页面是否包含指定文本。"""
        return text in self.page.content()

    def count(self, selector: str) -> int:
        """返回选择器匹配的元素数量。"""
        return self.page.locator(selector).count()

    def get_texts(self, selector: str) -> list[str]:
        """获取所有匹配元素的文本内容。"""
        return self.page.locator(selector).all_text_contents()

    def add_onboarding_completed(self) -> None:
        """预先标记新手引导已完成，避免弹窗阻塞。"""
        self.page.add_init_script("localStorage.setItem('onboarding_completed', 'true');")

    def assert_exactly_one_active_nav(self) -> None:
        """断言导航栏中只有一个高亮项。"""
        active_links = self.page.locator("nav a[class*='bg-primary']").count()
        assert active_links == 1, f"Expected exactly one active nav item, got {active_links}"
