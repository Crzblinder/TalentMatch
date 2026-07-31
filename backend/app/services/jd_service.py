"""JD 解析服务。"""

from __future__ import annotations

import base64
import logging
from typing import Any

from app.agents.jd_parser import JDParser
from app.config import Settings, get_settings
from app.llm.factory import LLMClientFactory
from app.utils.content_safety import check_text_safety

logger = logging.getLogger(__name__)


class JDService:
    def parse_jd_text(
        self,
        text: str,
        *,
        fuzzy: bool = False,
        prompt_variant: str | None = None,
    ) -> dict[str, Any]:
        """解析 JD 文本。

        Args:
            text: 原始 JD 文本
            fuzzy: 是否启用模糊识别（应届生友好模式）
            prompt_variant: 指定提示词变体
        """
        safety = check_text_safety(text, get_settings())
        if not safety.get("safe", True):
            labels = safety.get("labels", [])
            logger.warning("JD 文本内容安全检测未通过，labels: %s", labels)
            raise ValueError(
                f"JD 内容未通过安全检测，违规标签: {', '.join(labels) if labels else '未知'}"
            )

        variant = prompt_variant or ("fresh_graduate" if fuzzy else "default")
        parser = JDParser(prompt_variant=variant)
        return parser.parse_jd(text)

    def extract_text_from_image(self, file_bytes: bytes, ext: str, settings: Settings) -> str:
        """识别图片中的文本。

        优先级：
        1. 本地 OCR（rapidocr-onnxruntime），无需 API Key，开箱即用；
        2. 配置多模态 LLM 时，使用多模态模型进行二次识别；
        3. 均未配置时抛出清晰错误。
        """
        if ext not in ("png", "jpg", "jpeg", "webp", "gif"):
            raise ValueError(f"不支持的图片格式: {ext}")

        # 第一层：本地 OCR，零成本、无需网络
        try:
            from app.utils.ocr import extract_text_from_image as local_ocr_extract

            logger.info("图片识别：优先使用本地 OCR")
            raw_text = local_ocr_extract(file_bytes, ext)
            if raw_text.strip():
                return raw_text
            logger.warning("本地 OCR 未识别到文本，尝试多模态 LLM")
        except Exception as exc:
            logger.warning("本地 OCR 不可用: %s", exc)

        # 第二层：多模态 LLM（需配置 API Key）
        if (
            not settings.effective_multimodal_api_key
            or settings.effective_multimodal_api_key == "dummy"
        ):
            raise RuntimeError(
                "图片识别失败：本地 OCR 未返回文本，且未配置多模态 LLM API Key。"
                "请安装 rapidocr-onnxruntime 或配置 MULTIMODAL_API_KEY / OPENAI_API_KEY。"
            )

        logger.info("识别图片文件，使用多模态模型进行 OCR")
        base64_image = base64.b64encode(file_bytes).decode("utf-8")
        data_url = f"data:image/{ext};base64,{base64_image}"

        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="你是一名文档识别专家，请提取图片中的岗位描述文本内容。"),
            HumanMessage(
                content=[
                    {"type": "text", "text": "请识别图片中的岗位描述内容，提取所有文本信息："},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]
            ),
        ]

        llm = LLMClientFactory.create_multimodal(settings)
        try:
            response = llm.invoke(messages)
            raw_text = response.content if hasattr(response, "content") else str(response)
        except Exception as exc:
            logger.error("图片 OCR 识别失败: %s", exc)
            raise

        logger.info("图片 OCR 识别成功")
        return raw_text
