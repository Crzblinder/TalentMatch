"""布局/导航 Page Object。"""

from __future__ import annotations

from e2e.pages.base import BasePage
from playwright.sync_api import Page


class LayoutPage(BasePage):
    """封装侧边栏导航相关操作。"""

    def __init__(self, page: Page, root_url: str = "http://127.0.0.1:5173") -> None:
        super().__init__(page, root_url)

    def navigate_to(self, label: str) -> None:
        """点击导航标签进入对应页面。"""
        self.click_text(label)

    def is_nav_active(self, label: str) -> bool:
        """判断指定导航项是否处于高亮状态。"""
        link = self.page.locator("nav").locator("a", has_text=label)
        return link.count() == 1 and "bg-primary" in (link.get_attribute("class") or "")

    def open_mobile_menu(self) -> None:
        """移动端：打开顶部菜单。"""
        self.page.click("button[aria-label='打开菜单']")
