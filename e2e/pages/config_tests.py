"""配置检测页面 Page Object。"""

from __future__ import annotations

import re

from e2e.pages.base import BasePage
from playwright.sync_api import Page


class ConfigTestsPage(BasePage):
    """封装外部配置可用性检测页面操作。"""

    def __init__(self, page: Page, root_url: str = "http://127.0.0.1:5173") -> None:
        super().__init__(page, root_url)

    def open(self) -> None:
        """进入配置检测页面。"""
        self.goto("/config-tests")
        self.wait_for_text("外部配置可用性检测")

    def summary_card_values(self) -> dict[str, int]:
        """返回顶部汇总卡片的数值（总检测项/通过/失败/跳过）。"""
        cards = self.page.locator("[class*='grid-cols-4'] > div")
        texts = cards.all_text_contents()
        values: dict[str, int] = {}
        labels = {"总检测项", "通过", "失败", "跳过"}
        for text in texts:
            # 卡片文本格式：<标题>\n<number>\n[可能存在的图标标题]
            for label in labels:
                if label in text:
                    # 在标题之后查找第一个数字
                    after_label = text.split(label, 1)[-1]
                    match = re.search(r"\d+", after_label)
                    if match:
                        values[label] = int(match.group())
                    break
        return values

    def wait_for_summary_cards(self, timeout: int = 60_000) -> None:
        """等待汇总卡片渲染完成。"""
        self.page.wait_for_selector("text=总检测项", timeout=timeout)
        self.page.wait_for_selector("text=通过", timeout=timeout)
