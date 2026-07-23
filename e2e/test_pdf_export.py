"""E2E 测试：服务端 PDF 导出。

覆盖：
- 调用 /api/v1/reports/match/pdf 生成匹配报告 PDF
- 验证响应状态、Content-Type 与 PDF 文件头

运行方式：
    python e2e/test_pdf_export.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.with_server import server_context  # noqa: E402

BACKEND_URL = "http://127.0.0.1:8000"


def test_pdf_export_api() -> None:
    with server_context():
        payload = {
            "match_data": {
                "match_score": 0.85,
                "skill_score": 0.9,
                "experience_match": 0.8,
                "education_match": 1.0,
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": ["Kubernetes"],
                "transferable_skills": ["Flask"],
                "analysis_summary": "候选人与岗位高度匹配，仅缺失 Kubernetes 经验。",
            },
            "job_data": {
                "title": "Python 后端工程师",
                "company": {"name": "示例科技"},
                "city": "北京",
                "salary_min": 20000,
                "salary_max": 35000,
                "experience_level": "3-5年",
                "education_level": "本科",
            },
            "profile_data": {
                "name": "示例候选人",
                "experience_level": "3-5年",
                "skills": ["Python", "FastAPI", "Docker"],
                "target_job_titles": ["Python 后端工程师"],
            },
        }

        response = requests.post(
            f"{BACKEND_URL}/api/v1/reports/match/pdf",
            json=payload,
            timeout=60,
        )

        assert response.status_code == 200, (
            f"Expected status 200, got {response.status_code}: {response.text}"
        )
        assert response.headers.get("content-type") == "application/pdf", (
            f"Expected application/pdf, got {response.headers.get('content-type')}"
        )
        assert response.content.startswith(b"%PDF"), "Response does not look like a PDF file"
        assert len(response.content) > 1000, "PDF content seems too small"

        print(f"PDF export OK: {len(response.content)} bytes")
        print("PDF export E2E test passed.")


if __name__ == "__main__":
    test_pdf_export_api()
