"""简历编辑器/优化页面 Page Object。"""

from __future__ import annotations

from pathlib import Path

from e2e.pages.base import BasePage
from playwright.sync_api import Page


class ResumeEditorPage(BasePage):
    """封装简历优化页面操作。"""

    def __init__(self, page: Page, root_url: str = "http://127.0.0.1:5173") -> None:
        super().__init__(page, root_url)

    def open(self) -> None:
        """进入简历优化页面。"""
        self.goto("/resume-editor")
        self.wait_for_text("简历编辑器")

    def fill_jd_text(self, text: str) -> None:
        """填写目标岗位描述文本。"""
        self.fill_text(
            'textarea[placeholder="粘贴或上传岗位描述内容..."]',
            text,
        )

    def upload_resume(self, text_content: str) -> None:
        """通过文件选择器上传简历内容（创建临时 .docx 文件）。"""
        import tempfile

        from docx import Document

        with tempfile.NamedTemporaryFile(mode="w+b", suffix=".docx", delete=False) as f:
            temp_path = f.name
            document = Document()
            for line in text_content.splitlines():
                document.add_paragraph(line)
            document.save(temp_path)

        try:
            self.page.set_input_files(
                '[data-testid="resume-file-input"]',
                temp_path,
            )
            # 等待简历解析完成：简历解析结果区会出现"识别技能"
            self.wait_for_text("识别技能", timeout=15_000)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def click_optimize(self) -> None:
        """点击 AI 优化简历按钮。"""
        self.click('button:has-text("AI 优化简历")')

    def wait_for_optimization(self) -> None:
        """等待优化完成。"""
        self.wait_for_text("优化完成", timeout=30_000)
