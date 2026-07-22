"""内容安全检测与数据脱敏单元测试。"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.utils import content_safety as safety_module
from app.utils.content_safety import (
    check_text_safety,
    mask_resume_data,
    mask_sensitive_text,
)


def _settings(
    *,
    enable_content_safety: bool = False,
    alibaba_cloud_access_key_id: str = "",
    alibaba_cloud_access_key_secret: str = "",
    content_safety_endpoint: str = "green-cip.cn-shanghai.aliyuncs.com",
) -> Settings:
    return Settings(
        enable_content_safety=enable_content_safety,
        alibaba_cloud_access_key_id=alibaba_cloud_access_key_id,
        alibaba_cloud_access_key_secret=alibaba_cloud_access_key_secret,
        content_safety_endpoint=content_safety_endpoint,
    )


class TestMaskSensitiveText:
    def test_masks_phone_number(self) -> None:
        text = "联系电话：13800138000，请尽快联系。"
        assert mask_sensitive_text(text) == "联系电话：138****8000，请尽快联系。"

    def test_masks_multiple_phone_numbers(self) -> None:
        text = "13800138000 和 13912345678"
        assert mask_sensitive_text(text) == "138****8000 和 139****5678"

    def test_masks_id_card_18(self) -> None:
        text = "身份证号：110101199001011234"
        assert mask_sensitive_text(text) == "身份证号：110101**********1234"

    def test_masks_id_card_15(self) -> None:
        text = "身份证号：110101900101123"
        assert mask_sensitive_text(text) == "身份证号：110101**********1123"

    def test_masks_id_card_with_x(self) -> None:
        text = "身份证号：11010119900101121X"
        assert mask_sensitive_text(text) == "身份证号：110101**********121X"

    def test_leaves_normal_text_unchanged(self) -> None:
        text = "这是一段普通文本，没有敏感信息。"
        assert mask_sensitive_text(text) == text


class TestMaskResumeData:
    def test_masks_nested_string_values(self) -> None:
        resume: dict[str, Any] = {
            "basic_info": {
                "name": "张三",
                "phone": "13800138000",
                "id_card": "110101199001011234",
            },
            "work_experience": [
                {
                    "company": "示例公司",
                    "contact": "请联系 13912345678",
                }
            ],
            "skills": ["Python", "Java"],
            "age": 25,
        }
        masked = mask_resume_data(resume)
        assert masked["basic_info"]["phone"] == "138****8000"
        assert masked["basic_info"]["id_card"] == "110101**********1234"
        assert masked["work_experience"][0]["contact"] == "请联系 139****5678"
        assert masked["skills"] == ["Python", "Java"]
        assert masked["age"] == 25

    def test_returns_non_string_primitives_unchanged(self) -> None:
        assert mask_resume_data(123) == 123
        assert mask_resume_data(None) is None
        assert mask_resume_data([1, 2, 3]) == [1, 2, 3]


class TestCheckTextSafety:
    def test_returns_safe_when_disabled(self) -> None:
        settings = _settings(enable_content_safety=False)
        result = check_text_safety("任意文本", settings)
        assert result == {"safe": True, "labels": [], "suggestion": "pass"}

    def test_returns_safe_when_enabled_without_keys(self) -> None:
        settings = _settings(enable_content_safety=True)
        result = check_text_safety("任意文本", settings)
        assert result == {"safe": True, "labels": [], "suggestion": "pass"}

    def test_returns_unsafe_when_api_suggests_block(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = _settings(
            enable_content_safety=True,
            alibaba_cloud_access_key_id="ak-test",
            alibaba_cloud_access_key_secret="sk-test",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": 200,
            "data": [
                {
                    "results": [
                        {"label": "spam", "rate": 99.5, "suggestion": "block"},
                    ]
                }
            ],
        }

        def _fake_post(*args: Any, **kwargs: Any) -> MagicMock:
            return mock_response

        monkeypatch.setattr(safety_module.requests, "post", _fake_post)

        result = check_text_safety("违规广告内容", settings)
        assert result["safe"] is False
        assert "spam" in result["labels"]
        assert result["suggestion"] == "block"

    def test_returns_safe_when_api_suggests_review(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = _settings(
            enable_content_safety=True,
            alibaba_cloud_access_key_id="ak-test",
            alibaba_cloud_access_key_secret="sk-test",
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "code": 200,
            "data": [
                {
                    "results": [
                        {"label": "ad", "rate": 80.0, "suggestion": "review"},
                    ]
                }
            ],
        }

        def _fake_post(*args: Any, **kwargs: Any) -> MagicMock:
            return mock_response

        monkeypatch.setattr(safety_module.requests, "post", _fake_post)

        result = check_text_safety("疑似广告内容", settings)
        assert result["safe"] is True
        assert "ad" in result["labels"]
        assert result["suggestion"] == "review"

    def test_returns_safe_on_api_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        settings = _settings(
            enable_content_safety=True,
            alibaba_cloud_access_key_id="ak-test",
            alibaba_cloud_access_key_secret="sk-test",
        )

        def _fake_post(*args: Any, **kwargs: Any) -> MagicMock:
            raise RuntimeError("network error")

        monkeypatch.setattr(safety_module.requests, "post", _fake_post)

        result = check_text_safety("正常文本", settings)
        assert result == {"safe": True, "labels": [], "suggestion": "pass"}
