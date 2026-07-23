"""向量存储抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorStoreBase(ABC):
    """向量数据库统一接口，业务代码通过此接口与具体后端解耦。"""

    collection_name: str = "job_graph_knowledge"

    @abstractmethod
    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """插入或更新向量文档。"""
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        query_texts: list[str],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """查询相似向量。"""
        raise NotImplementedError

    @abstractmethod
    def delete_all(self) -> None:
        """删除集合中全部数据。"""
        raise NotImplementedError

    @abstractmethod
    def add_job_documents(self, jobs: list[Any]) -> int:
        """索引岗位文档，返回索引数量。"""
        raise NotImplementedError

    @abstractmethod
    def add_skill_documents(self, skills: list[Any]) -> int:
        """索引技能文档，返回索引数量。"""
        raise NotImplementedError

    @abstractmethod
    def query_similar(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """返回与 query 最相似的文档列表。"""
        raise NotImplementedError

    @abstractmethod
    def clear_collection(self) -> None:
        """清空集合。"""
        raise NotImplementedError
