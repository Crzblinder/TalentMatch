from __future__ import annotations

import logging

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """根据环境变量配置，实例化对应的 LangChain 统一 LLM 客户端。

    - USE_LOCAL_LLM=false（默认）→ ChatOpenAI（兼容 OpenAI / 第三方 OpenAI-compatible API）
    - USE_LOCAL_LLM=true          → ChatOllama（本地 Ollama 服务，零成本免密）
    - USE_DOMESTIC_LLM=true       → 优先使用国产 OpenAI-compatible API（DashScope / Zhipu）
    """

    @staticmethod
    def create(settings: Settings) -> BaseChatModel:
        """返回 LangChain BaseChatModel 实例，上层 Agent 无需关心底层实现。"""
        if settings.use_local_llm:
            try:
                from langchain_ollama import ChatOllama
            except ImportError as exc:
                raise ImportError(
                    "本地 Ollama 模式需要安装 langchain-ollama：pip install langchain-ollama>=0.3.0"
                ) from exc

            logger.info(
                "初始化 Ollama 客户端：model=%s, base_url=%s",
                settings.ollama_model,
                settings.ollama_base_url,
            )
            return ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=0.3,
            )

        from langchain_openai import ChatOpenAI

        if settings.use_domestic_llm and settings.dashscope_api_key:
            logger.info(
                "初始化 DashScope 客户端：model=%s, base_url=%s",
                settings.dashscope_model,
                settings.dashscope_base_url,
            )
            return ChatOpenAI(
                model=settings.dashscope_model,
                api_key=settings.dashscope_api_key,
                base_url=settings.dashscope_base_url,
                temperature=0.3,
                timeout=60.0,
            )

        if settings.use_domestic_llm and settings.zhipu_api_key:
            logger.info(
                "初始化 Zhipu 客户端：model=%s, base_url=%s",
                settings.zhipu_model,
                settings.zhipu_base_url,
            )
            return ChatOpenAI(
                model=settings.zhipu_model,
                api_key=settings.zhipu_api_key,
                base_url=settings.zhipu_base_url,
                temperature=0.3,
                timeout=60.0,
            )

        api_key = settings.openai_api_key or "dummy"
        logger.info(
            "初始化 OpenAI-compatible 客户端：model=%s, base_url=%s, has_key=%s",
            settings.openai_model,
            settings.openai_base_url,
            bool(settings.openai_api_key and settings.openai_api_key != "dummy"),
        )
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=api_key,
            base_url=settings.openai_base_url,
            temperature=0.3,
            timeout=60.0,
        )

    @staticmethod
    def create_multimodal(settings: Settings) -> BaseChatModel:
        """返回支持多模态（图片/OCR）的 LLM 客户端。

        使用专门的多模态模型配置，默认使用 GPT-4o，也可通过环境变量覆盖。
        开启国产模式时优先使用国产多模态模型（如 qwen-vl-max / glm-4v）。
        多模态 API Key 和 Base URL 默认回退到通用配置。
        """
        if settings.use_local_llm:
            logger.warning("Ollama 模式暂不支持多模态，降级到通用客户端")
            return LLMClientFactory.create(settings)

        from langchain_openai import ChatOpenAI

        if settings.use_domestic_llm:
            model = settings.domestic_multimodal_model
            if settings.dashscope_api_key:
                api_key = settings.dashscope_api_key
                base_url = settings.dashscope_base_url
            elif settings.zhipu_api_key:
                api_key = settings.zhipu_api_key
                base_url = settings.zhipu_base_url
            else:
                api_key = settings.effective_multimodal_api_key or "dummy"
                base_url = settings.effective_multimodal_base_url

            logger.info(
                "初始化国产多模态客户端：model=%s, base_url=%s, has_key=%s",
                model,
                base_url,
                bool(api_key and api_key != "dummy"),
            )
            return ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
                timeout=120.0,
            )

        api_key = settings.effective_multimodal_api_key or "dummy"
        base_url = settings.effective_multimodal_base_url
        model = settings.multimodal_model

        logger.info(
            "初始化多模态客户端：model=%s, base_url=%s, has_key=%s",
            model,
            base_url,
            bool(api_key and api_key != "dummy"),
        )
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
            timeout=120.0,
        )
