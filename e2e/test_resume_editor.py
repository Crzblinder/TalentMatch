"""E2E 测试：简历优化流程。

覆盖：
- 进入简历编辑器页面
- 上传简历文件（.docx）并解析
- 填写目标岗位描述
- 执行 AI 优化并查看结果

运行方式：
    python e2e/test_resume_editor.py
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
    ResumeEditorPage,
    find_chrome_executable,
)
from scripts.with_server import server_context  # noqa: E402

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".playwright-browsers"))


def test_resume_editor_flow() -> None:
    chrome = find_chrome_executable()
    if chrome is None:
        raise FileNotFoundError(
            "Playwright Chromium not found. "
            "Set PLAYWRIGHT_BROWSERS_PATH and run 'playwright install chromium'."
        )

    print(f"Using Chromium: {chrome}")

    resume_text = """张三
手机：13812345678
邮箱：zhangsan@example.com

教育经历
2016.09-2020.06 北京大学 计算机科学与技术 本科

工作经历
2020.07-2023.03 某科技有限公司 Python后端工程师
负责后端服务开发，使用 Python、FastAPI 和 PostgreSQL。

技能
Python、FastAPI、PostgreSQL、Docker

求职意向
期望岗位：Python后端工程师
"""
    jd_text = """某科技公司招聘 Python 后端工程师
岗位职责：负责后端服务开发。
岗位要求：熟悉 Python、FastAPI、PostgreSQL，3-5 年经验，本科及以上学历。"""

    with server_context():
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=str(chrome),
            )
            page = browser.new_page()
            base = BasePage(page)
            editor = ResumeEditorPage(page)

            try:
                base.add_onboarding_completed()

                # 1. 进入简历编辑器
                editor.open()
                print("Resume editor loaded.")

                # 2. 填写目标岗位描述
                editor.fill_jd_text(jd_text)
                print("Filled JD text.")

                # 3. 上传简历文件并解析
                editor.upload_resume(resume_text)
                print("Resume uploaded and parsed.")

                # 4. 执行 AI 优化
                editor.click_optimize()
                editor.wait_for_optimization()
                print("Resume optimization completed.")

                # 5. 验证优化结果展示
                assert editor.has_text("优化完成")
                assert editor.has_text("应用优化结果")
                print("Optimization result rendered.")

                print("Resume editor E2E test passed.")
            except Exception:
                base.screenshot_on_failure("resume_editor_failure")
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    test_resume_editor_flow()
