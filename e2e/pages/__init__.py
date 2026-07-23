"""E2E Page Object 模式公共模块。"""

from __future__ import annotations

from e2e.pages.base import BasePage, find_chrome_executable
from e2e.pages.config_tests import ConfigTestsPage
from e2e.pages.job_library import JobLibraryPage
from e2e.pages.job_match import JobMatchPage
from e2e.pages.layout import LayoutPage
from e2e.pages.resume_editor import ResumeEditorPage

__all__ = [
    "BasePage",
    "ConfigTestsPage",
    "JobLibraryPage",
    "JobMatchPage",
    "LayoutPage",
    "ResumeEditorPage",
    "find_chrome_executable",
]
