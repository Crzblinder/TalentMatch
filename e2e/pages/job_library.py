"""岗位库页面 Page Object。"""

from __future__ import annotations

from e2e.pages.base import BasePage
from playwright.sync_api import Page


class JobLibraryPage(BasePage):
    """封装岗位库/我的收藏页面操作。"""

    def __init__(self, page: Page, root_url: str = "http://127.0.0.1:5173") -> None:
        super().__init__(page, root_url)

    def open(self) -> None:
        """进入岗位库页面。"""
        self.goto("/jobs")
        self.wait_for_text("岗位库")

    def open_favorites(self) -> None:
        """进入我的收藏页面。"""
        self.goto("/favorites")
        self.wait_for_text("我的收藏")

    def search_job(self, query: str) -> None:
        """在岗位库搜索框中搜索指定岗位。"""
        self.page.fill("input[placeholder='搜索岗位关键词']", query)
        self.page.click("button:has-text('筛选')")
        # 等待表格刷新（骨架屏或空状态消失）
        self.page.wait_for_selector("table tbody tr", timeout=10_000)

    def job_rows(self) -> int:
        """返回岗位表格行数。"""
        return self.count("table tbody tr")

    def toggle_favorite(self, job_title: str) -> None:
        """点击指定岗位行的收藏/取消收藏按钮。"""
        row = self.page.locator("table tbody tr", has_text=job_title).first
        button = row.locator("button[aria-label='收藏'], button[aria-label='取消收藏']").first
        button.wait_for(state="visible", timeout=10_000)
        # 等待收藏按钮可用（加载完成后 disabled 属性消失）
        self.page.wait_for_function(
            """() => {
                const rows = Array.from(document.querySelectorAll('table tbody tr'));
                const row = rows.find(r => r.textContent.includes('""" + job_title + """'));
                if (!row) return false;
                const btn = row.querySelector('button[aria-label="收藏"], button[aria-label="取消收藏"]');
                return btn && !btn.disabled;
            }""",
            timeout=10_000,
        )
        button.click(timeout=10_000)

    def is_favorite_active(self, job_title: str) -> bool:
        """判断指定岗位是否已收藏（心形图标填充）。"""
        row = self.page.locator("table tbody tr", has_text=job_title).first
        heart = row.locator("svg").first
        return "fill-red-500" in (heart.get_attribute("class") or "")

    def wait_for_favorite_state(self, job_title: str, active: bool, timeout: int = 10_000) -> None:
        """等待指定岗位的收藏状态变为目标值。"""
        self.page.wait_for_function(
            """(args) => {
                const [title, wantActive] = args;
                const rows = Array.from(document.querySelectorAll('table tbody tr'));
                const row = rows.find(r => r.textContent.includes(title));
                if (!row) return false;
                const heart = row.querySelector('svg');
                if (!heart) return false;
                const isActive = heart.classList.contains('fill-red-500');
                return isActive === wantActive;
            }""",
            arg=[job_title, active],
            timeout=timeout,
        )

    def go_to_match(self, job_title: str) -> None:
        """点击指定岗位行的去匹配按钮。"""
        row = self.page.locator("table tbody tr", has_text=job_title).first
        row.locator("button:has-text('去匹配')").first.click()
