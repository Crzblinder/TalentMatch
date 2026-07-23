"""岗位匹配页面 Page Object。"""

from __future__ import annotations

from e2e.pages.base import BasePage
from playwright.sync_api import Page


class JobMatchPage(BasePage):
    """封装岗位匹配流程操作。"""

    def __init__(self, page: Page, root_url: str = "http://127.0.0.1:5173") -> None:
        super().__init__(page, root_url)

    def open(self) -> None:
        """进入岗位匹配页面。"""
        self.goto("/match")
        self.wait_for_text("岗位技能匹配")

    def fill_basic_info(self, name: str) -> None:
        """填写基本信息 Tab 的姓名。"""
        self.fill_text('input[placeholder="请输入姓名"]', name)

    def fill_skills(self, skills: str) -> None:
        """切换到技能优势 Tab 并填写技能。"""
        self.click_text("技能优势")
        self.fill_text(
            'textarea[placeholder="输入技能，用逗号分隔，例如：Python, MySQL, 数据分析"]',
            skills,
        )

    def go_to_next_step(self) -> None:
        """点击下一步。"""
        self.click('button:has-text("下一步")')
        self.wait_for_text("选择目标岗位")

    def select_first_job(self) -> None:
        """选择岗位表格中的第一个岗位（等待真实数据加载）。"""
        # 等待真实岗位行中的单选按钮出现（骨架屏中不含 radio）
        first_radio = self.page.locator("table tbody tr td input[type='radio']").first
        first_radio.wait_for(state="visible", timeout=15_000)
        # 点击第一行的单选按钮
        first_radio.click()
        # 等待行被标记为已选择
        self.page.wait_for_selector("table tbody tr[data-state='selected']")

    def start_match(self) -> None:
        """点击开始匹配并等待结果。"""
        # 确保按钮已启用
        self.page.wait_for_selector('button:has-text("开始匹配"):not([disabled])')
        self.click('button:has-text("开始匹配")')
        self.wait_for_text("匹配结果", timeout=45_000)

    def run_full_match(self, name: str, skills: str) -> None:
        """完成完整的匹配流程。"""
        self.fill_basic_info(name)
        self.fill_skills(skills)
        self.go_to_next_step()
        self.select_first_job()
        self.start_match()
