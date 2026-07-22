"""ResumeService 文档解析测试。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.services import resume_service as resume_module
from app.services.resume_service import ResumeService


def _settings(
    *,
    use_domestic_llm: bool = False,
    dashscope_api_key: str = "",
) -> Settings:
    return Settings(
        use_domestic_llm=use_domestic_llm,
        dashscope_api_key=dashscope_api_key,
        dashscope_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        dashscope_doc_parse_model="qwen-vl-max",
    )


def _patch_settings(monkeypatch: pytest.MonkeyPatch, **kwargs) -> Settings:
    settings = _settings(**kwargs)
    monkeypatch.setattr(resume_module, "get_settings", lambda: settings)
    return settings


def _mock_pdf_reader(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    page = MagicMock()
    page.extract_text.return_value = text
    reader = MagicMock()
    reader.pages = [page]
    monkeypatch.setattr(resume_module, "PdfReader", lambda _bytes: reader)


def _mock_document(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    paragraph = MagicMock()
    paragraph.text = text
    document = MagicMock()
    document.paragraphs = [paragraph]
    monkeypatch.setattr(resume_module, "Document", lambda _bytes: document)


class TestExtractTextFromPdf:
    def test_prefers_dashscope_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_settings(monkeypatch, use_domestic_llm=True, dashscope_api_key="sk-test")
        service = ResumeService()

        def _fake_parse(_file_bytes: bytes, _filename: str) -> str:
            return "cloud pdf text"

        monkeypatch.setattr(service, "_parse_with_dashscope", _fake_parse)

        result = service.extract_text_from_pdf(b"fake pdf bytes")
        assert result == "cloud pdf text"

    def test_falls_back_to_local_on_cloud_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_settings(monkeypatch, use_domestic_llm=True, dashscope_api_key="sk-test")
        service = ResumeService()

        def _raise_cloud_failure(_file_bytes: bytes, _filename: str) -> str:
            raise RuntimeError("cloud failed")

        monkeypatch.setattr(service, "_parse_with_dashscope", _raise_cloud_failure)
        _mock_pdf_reader(monkeypatch, "local pdf text")

        result = service.extract_text_from_pdf(b"fake pdf bytes")
        assert result == "local pdf text"

    def test_uses_local_when_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_settings(monkeypatch, use_domestic_llm=True, dashscope_api_key="")
        service = ResumeService()
        _mock_pdf_reader(monkeypatch, "local pdf text")

        result = service.extract_text_from_pdf(b"fake pdf bytes")
        assert result == "local pdf text"


class TestExtractTextFromDocx:
    def test_prefers_dashscope_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_settings(monkeypatch, use_domestic_llm=True, dashscope_api_key="sk-test")
        service = ResumeService()

        def _fake_parse(_file_bytes: bytes, _filename: str) -> str:
            return "cloud docx text"

        monkeypatch.setattr(service, "_parse_with_dashscope", _fake_parse)

        result = service.extract_text_from_docx(b"fake docx bytes")
        assert result == "cloud docx text"

    def test_falls_back_to_local_on_cloud_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_settings(monkeypatch, use_domestic_llm=True, dashscope_api_key="sk-test")
        service = ResumeService()

        def _raise_cloud_failure(_file_bytes: bytes, _filename: str) -> str:
            raise RuntimeError("cloud failed")

        monkeypatch.setattr(service, "_parse_with_dashscope", _raise_cloud_failure)
        _mock_document(monkeypatch, "local docx text")

        result = service.extract_text_from_docx(b"fake docx bytes")
        assert result == "local docx text"

    def test_uses_local_when_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_settings(monkeypatch, use_domestic_llm=True, dashscope_api_key="")
        service = ResumeService()
        _mock_document(monkeypatch, "local docx text")

        result = service.extract_text_from_docx(b"fake docx bytes")
        assert result == "local docx text"
