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
        """使用多模态模型识别图片中的 JD 文本。

        开启国产模式时优先调用国产多模态模型；识别失败时自动回退到
        OpenAI 多模态模型，确保可用性。
        """
        if ext not in ("png", "jpg", "jpeg", "webp", "gif"):
            raise ValueError(f"不支持的图片格式: {ext}")

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
            if settings.use_domestic_llm:
                logger.warning("国产多模态 OCR 失败，回退到 OpenAI 多模态: %s", exc)
                from langchain_openai import ChatOpenAI

                fallback_llm = ChatOpenAI(
                    model=settings.multimodal_model,
                    api_key=settings.effective_multimodal_api_key or "dummy",
                    base_url=settings.effective_multimodal_base_url,
                    temperature=0.2,
                    timeout=120.0,
                )
                response = fallback_llm.invoke(messages)
                raw_text = response.content if hasattr(response, "content") else str(response)
            else:
                logger.error("图片 OCR 识别失败: %s", exc)
                raise

        logger.info("图片 OCR 识别成功")
        return raw_text
