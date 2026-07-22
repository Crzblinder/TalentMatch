"""向量存储入口：根据配置返回 Chroma 或 Qdrant 适配器。"""

from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.rag.vector_store_base import VectorStoreBase

logger = logging.getLogger(__name__)

# 保持向后兼容：VectorStore 仍指向 Chroma 实现
from app.rag.vector_store_chroma import ChromaVectorStore as VectorStore  # noqa: F401

_vector_store: VectorStoreBase | None = None


def get_vector_store() -> VectorStoreBase:
    """根据配置返回向量存储适配器单例。

    默认使用本地 Chroma，生产环境可切换为 Qdrant。
    """
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        provider = settings.vector_db_provider.lower()

        if provider == "qdrant":
            logger.info("使用 Qdrant 向量存储: %s", settings.qdrant_url)
            from app.rag.vector_store_qdrant import QdrantVectorStore

            _vector_store = QdrantVectorStore("job_graph_knowledge")
        else:
            if provider != "chroma":
                logger.warning("未知的 VECTOR_DB_PROVIDER=%s，降级为 chroma", provider)
            logger.info("使用本地 Chroma 向量存储: %s", settings.vector_db_path)
            from app.rag.vector_store_chroma import ChromaVectorStore

            _vector_store = ChromaVectorStore("job_graph_knowledge")

    return _vector_store
